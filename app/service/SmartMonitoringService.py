# -*- coding: utf-8 -*-
"""
智能监控服务
整合YOLO检测、规则引擎和AI推理决策
"""
import copy
import time
import queue
from collections import deque
import numpy as np
import cv2
from threading import Lock, Thread
from typing import Dict, Optional
from app.model.YoloModel import YoloModel
from app.alert.rule_engine import RuleEngine
from app.ai.reasoning_engine import ReasoningEngine
from app.config.config import Config
from app.service.event_trigger import EventTrigger
from app.util.video_fs import file_frame_period_seconds


class SmartMonitoringService:
    """智能监控服务"""

    def __init__(self,
                 model_path: str,
                 src_points: np.ndarray,
                 cap,
                 rule_engine: RuleEngine,
                 reasoning_engine: Optional[ReasoningEngine] = None,
                 ai_requested: bool = False,
                 hot_zone=None,
                 stay_threshold=5,
                 traffic_flow=False,
                 num_lanes=2,
                 loop_file=False,
                 cap_type: str = "file"):
        """
        初始化智能监控服务

        Args:
            model_path: YOLO模型路径
            src_points: 透视变换源点
            cap: 视频捕获对象
            rule_engine: 规则引擎实例
            reasoning_engine: 推理引擎实例（可选）
            hot_zone: 热区多边形
            stay_threshold: 停留阈值（秒）
            traffic_flow: 是否启用交通流量统计
            num_lanes: 车道数量
            loop_file: 本地文件源时在片尾自动从头循环，避免采集线程退出导致画面卡住
        """
        self.model = YoloModel(model_path, src_points, hot_zone, stay_threshold, traffic_flow, num_lanes)
        self.loop_file = loop_file
        self.cap_type = cap_type
        self._file_frame_period = (
            file_frame_period_seconds(cap) if cap_type == "file" else 0.0
        )
        self.rule_engine = rule_engine
        self.reasoning_engine = reasoning_engine
        # 启动请求里是否勾选「启用 DeepSeek」（与是否已配置 API 密钥无关）
        self.ai_requested = bool(ai_requested)

        self.rowQueue = queue.Queue(maxsize=Config.FRAME_QUEUE_SIZE)
        self.processedQueue = queue.Queue(maxsize=Config.FRAME_QUEUE_SIZE)
        self.birdViewQueue = queue.Queue(maxsize=Config.FRAME_QUEUE_SIZE)
        self.reasoningQueue = queue.Queue(maxsize=Config.REASONING_QUEUE_SIZE)

        self.cap = cap
        self.frame_lock = Lock()  # 保护 last_*，避免与 HTTP 取帧竞态
        self._alert_history_lock = Lock()
        self._alert_seq = 0
        self.alert_history: deque = deque(maxlen=int(getattr(Config, "ALERT_HISTORY_MAX", 200) or 200))
        self.running = False
        self.event_trigger = EventTrigger(
            fixed_interval_seconds=Config.LLM_FIXED_INTERVAL_SECONDS,
            min_alert_count=Config.LLM_MIN_ALERT_COUNT,
            scene_change_threshold=Config.LLM_SCENE_CHANGE_THRESHOLD,
            enable_fixed_interval=Config.LLM_ENABLE_FIXED_INTERVAL,
            force_risk_levels=Config.LLM_FORCE_TRIGGER_RISK_LEVELS,
        )
        self.latest_decision = None
        self.latest_trigger_reason = "startup"
        self.latest_rules_result = None
        self.last_scene_snapshot = None
        self.reasoning_thread = None
        self.last_processed_frame = None
        self.last_row_frame = None
        self.last_bird_frame = None
        # 仅保留最新待推理帧，避免推理慢时积压导致画面滞后
        self.infer_queue: queue.Queue = queue.Queue(maxsize=1)
        self._capture_thread: Optional[Thread] = None
        self._infer_thread: Optional[Thread] = None
        self._last_heartbeat_ts = 0.0
        # 运行状态快照（不入告警队列），避免轮询消费队列时条目忽有忽无、界面闪烁
        self.latest_monitor_status: Optional[Dict] = None

    def try_put(self, q, item):
        """尝试放入队列，满则丢弃最旧"""
        try:
            q.put_nowait(item)
        except queue.Full:
            if not q.empty():
                q.get_nowait()
            q.put_nowait(item)

    @staticmethod
    def _redact_decision_for_history(decision):
        """历史记录里不保留处置建议/立即行动等长文本，避免列表臃肿。"""
        if not isinstance(decision, dict):
            return decision
        fd = decision.get("final_decision")
        new_fd = None
        if isinstance(fd, dict):
            new_fd = {
                k: v
                for k, v in fd.items()
                if k not in ("suggestions", "immediate_actions")
            }
        out = {k: v for k, v in decision.items() if k != "final_decision"}
        out["final_decision"] = new_fd if new_fd is not None else fd
        return out

    def _record_alert(self, payload: Dict) -> None:
        """追加一条告警历史（GET 只读快照，不消费）。"""
        rec = {**payload}
        if rec.get("decision") is not None:
            rec["decision"] = self._redact_decision_for_history(rec["decision"])
        with self._alert_history_lock:
            self._alert_seq += 1
            rec["alert_seq"] = self._alert_seq
            rec["recorded_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.alert_history.append(rec)

    @staticmethod
    def _clone_frame(frame):
        return frame.copy() if isinstance(frame, np.ndarray) else frame

    def _last_processed_is_none(self):
        with self.frame_lock:
            return self.last_processed_frame is None

    def _enqueue_infer(self, frame_count: int, timestamp: float, frame: np.ndarray) -> None:
        item = (frame_count, timestamp, self._clone_frame(frame))
        try:
            self.infer_queue.put_nowait(item)
        except queue.Full:
            try:
                self.infer_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.infer_queue.put_nowait(item)
            except queue.Full:
                pass

    def _signal_infer_shutdown(self) -> None:
        try:
            self.infer_queue.put_nowait(None)
        except queue.Full:
            try:
                self.infer_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.infer_queue.put_nowait(None)
            except queue.Full:
                pass

    def _update_monitor_status_snapshot(self, timestamp: float, scene_data: Dict, rules_result: Dict) -> None:
        """定期刷新运行状态快照（覆盖同一条目，不写入告警历史）。"""
        vc = int(scene_data.get("vehicle_count") or 0)
        wc = int(scene_data.get("worker_count") or 0)
        risk = (rules_result or {}).get("risk_level") or "low"
        raw_alerts = (rules_result or {}).get("alerts") or []
        ac = len(raw_alerts)
        ai_active = bool(self.reasoning_engine)
        if ai_active:
            deepseek_line = "DeepSeek：已启用（按事件频率调用）"
        elif self.ai_requested:
            deepseek_line = (
                "DeepSeek：已在界面勾选启用，但未检测到 API 密钥；"
                "请配置环境变量 DEEPSEEK_API_KEY 后重启后端"
            )
        else:
            deepseek_line = "DeepSeek：未在界面勾选启用"
        parts = [
            f"监控运行中：车辆约 {vc}，工人 {wc}，规则风险 {risk}，当期规则告警 {ac} 条。",
            deepseek_line,
        ]
        if ai_active:
            client = getattr(self.reasoning_engine, "deepseek_client", None)
            err = getattr(client, "last_error", None) if client else None
            if err:
                short = str(err).replace("\n", " ")
                if len(short) > 120:
                    short = short[:117] + "..."
                parts.append(f"最近接口状态：{short}")
        msg = "".join(parts)
        display_rules = {
            "risk_level": risk,
            "alert_count": 1,
            "alerts": [
                {
                    "rule_id": "SYS-STATUS",
                    "type": "status",
                    "level": "low",
                    "message": msg,
                }
            ],
        }
        self.latest_monitor_status = {
            "stable_id": "monitor-status",
            "timestamp": timestamp,
            "rules_result": display_rules,
            "decision": self.latest_decision,
            "trigger_reason": "heartbeat",
        }

    def _resize_if_needed(self, frame):
        if not Config.ENABLE_FRAME_RESIZE or frame is None:
            return frame
        height, width = frame.shape[:2]
        if width <= Config.MAX_FRAME_WIDTH:
            return frame
        scale = Config.MAX_FRAME_WIDTH / float(width)
        new_size = (int(width * scale), int(height * scale))
        return cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)

    def _start_reasoning_worker(self):
        if not self.reasoning_engine or self.reasoning_thread:
            return

        self.reasoning_thread = Thread(target=self._reasoning_loop, daemon=True)
        self.reasoning_thread.start()

    def _reasoning_loop(self):
        while self.running:
            try:
                payload = self.reasoningQueue.get(timeout=0.5)
            except queue.Empty:
                continue

            if payload is None:
                break

            try:
                decision = self.reasoning_engine.make_decision(
                    payload["scene_data"],
                    payload["rules_result"],
                )
                self.latest_decision = decision
                self.latest_trigger_reason = payload.get("trigger_reason", "unknown")

                display_rules = self._merge_deepseek_into_rules_display(
                    payload["rules_result"],
                    decision,
                )
                self._record_alert({
                    "timestamp": payload["scene_data"].get("timestamp"),
                    "rules_result": display_rules,
                    "decision": decision,
                    "trigger_reason": payload.get("trigger_reason", "unknown"),
                })
            except Exception as e:
                print(f"[SmartMonitoring] 推理线程异常: {e}")

    def _capture_loop(self):
        """独立线程持续拉流并刷新预览，不因 YOLO 阻塞而卡画面"""
        n = max(Config.PROCESS_EVERY_N_FRAMES, 1)
        frame_count = 0
        try:
            while self.running:
                t0 = time.perf_counter()
                ret, frame = self.cap.read()
                if not ret and self.loop_file:
                    try:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    except Exception:
                        pass
                    ret, frame = self.cap.read()
                if not ret:
                    if Config.DEBUG:
                        print("[SmartMonitoring] 视频流结束或无法循环播放")
                    break

                frame_count += 1
                timestamp = time.time()
                frame = self._resize_if_needed(frame)
                row = self._clone_frame(frame)
                with self.frame_lock:
                    self.last_row_frame = self._clone_frame(row)

                should_process = (
                    frame_count == 1
                    or frame_count % n == 0
                    or self._last_processed_is_none()
                )
                if should_process:
                    self._enqueue_infer(frame_count, timestamp, frame)

                if self._file_frame_period > 0:
                    elapsed = time.perf_counter() - t0
                    wait = self._file_frame_period - elapsed
                    if wait > 0:
                        time.sleep(wait)
        finally:
            self.running = False
            self._signal_infer_shutdown()

    def _inference_loop(self):
        """独立线程做检测与规则，与采集并行"""
        while True:
            try:
                item = self.infer_queue.get(timeout=0.5)
            except queue.Empty:
                if not self.running:
                    break
                continue
            if item is None:
                break
            frame_count, timestamp, frame = item
            try:
                processed, row, birdView = self.model.track(frame)
                scene_data = self._build_scene_data(timestamp, frame_count)
                self.last_scene_snapshot = scene_data
                rules_result = self.rule_engine.evaluate(scene_data)
                self.latest_rules_result = rules_result
                triggered, trigger_reason = self.event_trigger.should_trigger(scene_data, rules_result)
                if self.reasoning_engine and triggered:
                    self.try_put(self.reasoningQueue, {
                        "scene_data": scene_data,
                        "rules_result": rules_result,
                        "trigger_reason": trigger_reason,
                    })
                elif rules_result.get("alerts"):
                    self._record_alert({
                        "timestamp": timestamp,
                        "rules_result": rules_result,
                        "decision": self.latest_decision,
                        "trigger_reason": trigger_reason,
                    })
                hb_sec = float(getattr(Config, "ALERT_HEARTBEAT_SECONDS", 0) or 0)
                if hb_sec > 0 and (timestamp - self._last_heartbeat_ts) >= hb_sec:
                    self._last_heartbeat_ts = timestamp
                    self._update_monitor_status_snapshot(timestamp, scene_data, rules_result)
                processed = self._render_overlay(processed, rules_result, self.latest_decision)
                birdView = self._render_overlay(birdView, rules_result, self.latest_decision, anchor=(12, 24))
                with self.frame_lock:
                    self.last_processed_frame = self._clone_frame(processed)
                    self.last_row_frame = self._clone_frame(row)
                    self.last_bird_frame = self._clone_frame(birdView)
            except Exception as e:
                print(f"[SmartMonitoring] 推理管线异常: {e}")

    def start(self):
        """启动监控服务（采集线程 + 推理线程）"""
        self.running = True
        self._start_reasoning_worker()
        try:
            if Config.DEBUG:
                print("[SmartMonitoring] 启动智能监控服务")
            self._capture_thread = Thread(target=self._capture_loop, daemon=True)
            self._infer_thread = Thread(target=self._inference_loop, daemon=True)
            self._capture_thread.start()
            self._infer_thread.start()
            self._capture_thread.join()
            self._infer_thread.join()
        except Exception as e:
            print(f"[SmartMonitoring] 处理异常: {e}")
        finally:
            self.release()

    def stop(self):
        """停止监控服务"""
        self.running = False

    def _build_scene_data(self, timestamp: float, frame_count: int) -> Dict:
        """构建场景数据用于规则评估"""
        stats = self.model.get_statistics()
        model_scene = self.model.get_scene_data()

        scene_data = {
            "timestamp": timestamp,
            "frame_count": frame_count,
            "vehicle_count": stats.get("total_count", 0),
            "worker_count": len(model_scene.get("workers", [])),
            "vehicles": model_scene.get("vehicles", []),
            "workers": model_scene.get("workers", []),
            "equipment": model_scene.get("equipment", []),
            "objects": model_scene.get("objects", []),
            "danger_zone_objects": model_scene.get("danger_zone_objects", []),
            "fast_vehicles": model_scene.get("fast_vehicles", []),
            "abnormal_stays": model_scene.get("abnormal_stays", []),
        }

        return scene_data

    def get_statistics(self):
        """获取统计信息"""
        stats = self.model.get_statistics()
        stats["latest_risk_level"] = (self.latest_rules_result or {}).get("risk_level", "low")
        stats["latest_trigger_reason"] = self.latest_trigger_reason
        return stats

    def get_row_frame(self):
        """获取原始帧（拷贝，避免与处理线程共享缓冲区）"""
        with self.frame_lock:
            if self.last_row_frame is not None:
                return self.last_row_frame.copy()
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def get_processed_frame(self):
        """获取处理后的帧；推理尚未完成时返回当前原画，避免黑屏"""
        with self.frame_lock:
            if self.last_processed_frame is not None:
                return self.last_processed_frame.copy()
            if self.last_row_frame is not None:
                return self.last_row_frame.copy()
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def get_birdView_frame(self):
        """获取鸟瞰图帧"""
        with self.frame_lock:
            if self.last_bird_frame is not None:
                return self.last_bird_frame.copy()
        return np.zeros((800, 500, 3), dtype=np.uint8)

    def get_latest_alerts(self, max_count: int = 10) -> list:
        """返回告警历史快照（新→旧），不修改历史。运行状态见 get_live_monitor_status。"""
        n = max(1, int(max_count))
        with self._alert_history_lock:
            tail = list(self.alert_history)[-n:]
        return list(reversed(tail))

    def get_live_monitor_status(self) -> Optional[Dict]:
        """当前运行状态（心跳刷新），不写入告警历史；供界面单独展示。"""
        snap = self.latest_monitor_status
        return copy.deepcopy(snap) if snap else None

    def get_latest_decision(self):
        return self.latest_decision

    @staticmethod
    def _risk_level_rank(level: str) -> int:
        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        return order.get(str(level or "low").lower(), 0)

    @classmethod
    def _merge_risk_levels(cls, a: str, b: Optional[str]) -> str:
        if not b:
            return a or "low"
        labels = ["low", "medium", "high", "critical"]
        ia = cls._risk_level_rank(a)
        ib = cls._risk_level_rank(b)
        return labels[max(ia, ib)]

    def _merge_deepseek_into_rules_display(self, rules_result: Dict, decision: Dict) -> Dict:
        """把 DeepSeek 的 risks/建议/推理并入 rules_result.alerts，便于「最新告警」列表展示。"""
        rr = {**rules_result, "alerts": list(rules_result.get("alerts", []))}
        fd = decision.get("final_decision") or {}
        ai = decision.get("ai_analysis")
        ai = ai if isinstance(ai, dict) else {}

        risks = fd.get("ai_risks")
        if risks is None:
            risks = ai.get("risks")
        if risks is None:
            risks = []
        elif isinstance(risks, str):
            risks = [risks]
        elif not isinstance(risks, list):
            risks = [str(risks)]
        for i, text in enumerate(risks):
            t = str(text).strip()
            if not t:
                continue
            lvl = fd.get("risk_level") or ai.get("risk_level") or "medium"
            rr["alerts"].append({
                "rule_id": f"DeepSeek-R{i}",
                "type": "deepseek_risk",
                "level": lvl if str(lvl).lower() in ("low", "medium", "high", "critical") else "medium",
                "message": f"[DeepSeek] {t}",
            })

        reasoning = fd.get("reasoning") or ai.get("reasoning")
        if reasoning and str(reasoning).strip():
            s = str(reasoning).strip()
            if len(s) > 300:
                s = s[:297] + "…"
            rr["alerts"].append({
                "rule_id": "DeepSeek-推理",
                "type": "deepseek_reasoning",
                "level": "low",
                "message": f"[DeepSeek 推理] {s}",
            })
        elif ai.get("analysis"):
            s = str(ai.get("analysis")).strip()[:400]
            rr["alerts"].append({
                "rule_id": "DeepSeek-原文",
                "type": "deepseek_raw",
                "level": "medium",
                "message": f"[DeepSeek] {s}",
            })

        for i, sug in enumerate(fd.get("suggestions") or []):
            t = str(sug).strip()
            if t:
                rr["alerts"].append({
                    "rule_id": f"DeepSeek-建议{i}",
                    "type": "deepseek_suggestion",
                    "level": "low",
                    "message": f"[DeepSeek 建议] {t}",
                })

        if decision.get("ai_analysis") is None:
            err = decision.get("ai_error") or "未知错误"
            rr["alerts"].append({
                "rule_id": "DeepSeek-未响应",
                "type": "deepseek_error",
                "level": "medium",
                "message": f"DeepSeek 未返回有效结果。详情：{err}（请核对环境变量 DEEPSEEK_API_KEY 或 config 中的密钥、代理与防火墙）",
            })
        elif not risks and not reasoning and not ai.get("analysis") and not (fd.get("suggestions") or []):
            rr["alerts"].append({
                "rule_id": "DeepSeek-提示",
                "type": "deepseek_info",
                "level": "low",
                "message": "[DeepSeek] 已调用；返回 JSON 中无 risks/建议字段，可在提示词中要求模型必填 risks。",
            })

        rr["alert_count"] = len(rr["alerts"])
        rr["risk_level"] = self._merge_risk_levels(
            rules_result.get("risk_level", "low"),
            fd.get("risk_level") or ai.get("risk_level"),
        )
        return rr

    def _render_overlay(self, frame, rules_result: Optional[Dict], decision: Optional[Dict], anchor=(12, 36)):
        """不在画面上叠加规则/AI 建议等文字，仅保留检测框等几何绘制。"""
        return frame

    def release(self):
        """释放资源"""
        self.running = False
        self.latest_monitor_status = None
        with self._alert_history_lock:
            self.alert_history.clear()
            self._alert_seq = 0
        self._signal_infer_shutdown()
        try:
            self.cap.release()
        except Exception:
            pass
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=4)
        if self._infer_thread and self._infer_thread.is_alive():
            self._infer_thread.join(timeout=30)
        if self.reasoning_thread and self.reasoning_thread.is_alive():
            self.try_put(self.reasoningQueue, None)
            self.reasoning_thread.join(timeout=2)
        self.model.reset_statistics()
        with self.frame_lock:
            self.last_processed_frame = None
            self.last_row_frame = None
            self.last_bird_frame = None
