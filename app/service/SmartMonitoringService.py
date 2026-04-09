# -*- coding: utf-8 -*-
"""
智能监控服务
整合YOLO检测、规则引擎和AI推理决策
"""
import time
import queue
import numpy as np
from threading import Lock
from typing import Dict, Optional
from app.model.YoloModel import YoloModel
from app.alert.rule_engine import RuleEngine
from app.ai.reasoning_engine import ReasoningEngine


class SmartMonitoringService:
    """智能监控服务"""

    def __init__(self,
                 model_path: str,
                 src_points: np.ndarray,
                 cap,
                 rule_engine: RuleEngine,
                 reasoning_engine: Optional[ReasoningEngine] = None,
                 hot_zone=None,
                 stay_threshold=5,
                 traffic_flow=False,
                 num_lanes=2):
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
        """
        self.model = YoloModel(model_path, src_points, hot_zone, stay_threshold, traffic_flow, num_lanes)
        self.rule_engine = rule_engine
        self.reasoning_engine = reasoning_engine

        self.rowQueue = queue.Queue(maxsize=10)
        self.processedQueue = queue.Queue(maxsize=10)
        self.birdViewQueue = queue.Queue(maxsize=10)
        self.alertQueue = queue.Queue(maxsize=50)  # 告警队列

        self.cap = cap
        self.frame_lock = Lock()
        self.running = False

    def try_put(self, q, item):
        """尝试放入队列，满则丢弃最旧"""
        try:
            q.put_nowait(item)
        except queue.Full:
            if not q.empty():
                q.get_nowait()
            q.put_nowait(item)

    def start(self):
        """启动监控服务"""
        self.running = True
        try:
            print(f"[SmartMonitoring] 启动智能监控服务")
            frame_count = 0

            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("[SmartMonitoring] 视频流结束")
                    break

                frame_count += 1
                timestamp = time.time()

                # YOLO检测和跟踪
                processed, row, birdView = self.model.track(frame)

                # 构建场景数据
                scene_data = self._build_scene_data(timestamp, frame_count)

                # 规则引擎评估
                rules_result = self.rule_engine.evaluate(scene_data)

                # AI推理决策（如果配置）
                decision = None
                if self.reasoning_engine:
                    decision = self.reasoning_engine.make_decision(scene_data, rules_result)

                # 将告警放入队列
                if rules_result.get("alerts"):
                    self.try_put(self.alertQueue, {
                        "timestamp": timestamp,
                        "rules_result": rules_result,
                        "decision": decision
                    })

                # 放入帧队列
                self.try_put(self.processedQueue, processed)
                self.try_put(self.rowQueue, row)
                self.try_put(self.birdViewQueue, birdView)

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

        # 简化版场景数据，实际应从跟踪结果提取详细信息
        scene_data = {
            "timestamp": timestamp,
            "frame_count": frame_count,
            "vehicle_count": stats.get("total_count", 0),
            "worker_count": 0,  # 需要扩展YOLO模型支持人员检测
            "vehicles": [],  # 需要从track_history提取
            "workers": [],
            "danger_zone_objects": [],
            "fast_vehicles": [],
            "abnormal_stays": list(self.model.long_stay_ids)
        }

        return scene_data

    def get_statistics(self):
        """获取统计信息"""
        return self.model.get_statistics()

    def get_row_frame(self):
        """获取原始帧"""
        if not self.rowQueue.empty():
            return self.rowQueue.get()
        return None

    def get_processed_frame(self):
        """获取处理后的帧"""
        if not self.processedQueue.empty():
            return self.processedQueue.get()
        return None

    def get_birdView_frame(self):
        """获取鸟瞰图帧"""
        if not self.birdViewQueue.empty():
            return self.birdViewQueue.get()
        return None

    def get_latest_alerts(self, max_count: int = 10) -> list:
        """获取最新告警"""
        alerts = []
        while not self.alertQueue.empty() and len(alerts) < max_count:
            alerts.append(self.alertQueue.get())
        return alerts

    def release(self):
        """释放资源"""
        self.running = False
        self.cap.release()
        self.model.reset_statistics()
