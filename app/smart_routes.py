# -*- coding: utf-8 -*-
"""
智能监控路由
支持规则引擎和AI推理决策的API接口
"""
import os
import cv2
import threading
import numpy as np
from functools import wraps
from app.util.Camera import Camera
from app.util.video_fs import list_video_files, resolve_safe_video_file
from app.service.SmartMonitoringService import SmartMonitoringService
from app.alert.rule_engine import (
    RuleEngine,
    WorkerInDangerZoneRule,
    VehicleSpeedingRule,
    VehicleWorkerProximityRule
)
from app.ai.deepseek_client import DeepSeekClient
from app.ai.reasoning_engine import ReasoningEngine
from app.config.config import Config
import json
from flask import request, Blueprint, jsonify, Response


def _coerce_bool(value, default=False):
    """解析 JSON / 表单里的布尔值，避免字符串 \"true\" 被当成真。"""
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        s = value.strip().lower()
        if s in ("1", "true", "yes", "on"):
            return True
        if s in ("0", "false", "no", "off", ""):
            return False
    return bool(value)


# 装饰器：需要运行中的服务
def with_service(func):
    @wraps(func)
    def wrapper(service_id, *args, **kwargs):
        try:
            service_info = smart_services.get(service_id)
            if not service_info or 'service' not in service_info:
                return jsonify({"error": "Service not found"}), 400
            service = service_info['service']
            return func(service, *args, **kwargs)
        except Exception as e:
            return jsonify({"error": f"Internal error: {str(e)}"}), 500
    return wrapper


# 创建Blueprint
smart_api_bp = Blueprint('smart_api', __name__)

# 存储多个智能监控服务实例
smart_services = {}

# 服务ID管理
current_service_id = 0
id_lock = threading.Lock()
thread_lock = threading.Lock()


# 工具函数：发送帧响应
def send_frame_response(frame):
    if frame is None:
        return jsonify({"error": "No frame available"}), 400

    if isinstance(frame, np.ndarray):
        ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(Config.JPEG_QUALITY)])
        if not ret:
            return jsonify({"error": "Failed to encode frame"}), 500
        frame = jpeg.tobytes()

    if not isinstance(frame, bytes):
        return jsonify({"error": "Invalid frame format"}), 500

    return Response(frame, mimetype='image/jpeg')


# 路由：获取视频文件列表
@smart_api_bp.route('/fileList', methods=['GET'])
def fileList():
    return jsonify({"file_list": list_video_files()}), 200


# 路由：获取单帧
@smart_api_bp.route('/getOneFrame', methods=['POST'])
def get_one_frame():
    cap_type = request.json.get('cap_type')
    cap_path = request.json.get('cap_path')
    if cap_type == 'file':
        safe = resolve_safe_video_file(cap_path)
        if not safe:
            return jsonify({"error": "无效的视频路径"}), 400
        cap_path = safe
    cap = Camera()
    cap.setCap(cap_type, cap_path)
    if not cap.getCap().isOpened():
        return jsonify({"error": "无法打开视频源"}), 400

    ret, frame = cap.getCap().read()
    cap.getCap().release()

    if not ret:
        return jsonify({"error": "Failed to capture frame"}), 500

    return send_frame_response(frame)


# 路由：启动智能监控服务
@smart_api_bp.route('/start', methods=['POST'])
def start_smart_service():
    if not request.json or 'src_points' not in request.json:
        return jsonify({"error": "必须提供src_points参数"}), 400

    src_points = request.json.get('src_points')
    cap_type = request.json.get('cap_type')
    cap_path = request.json.get('cap_path')
    danger_zones = request.json.get('danger_zones', [])  # 危险区域配置
    enable_ai = _coerce_bool(
        request.json.get("enable_ai"),
        default=bool(getattr(Config, "DEEPSEEK_ENABLED", False)),
    )

    # 参数验证
    if not src_points or len(src_points) < 4:
        return jsonify({"error": "至少需要4个源点坐标"}), 400
    if not cap_type or not cap_path:
        return jsonify({"error": "必须提供capture类型和路径"}), 400

    if cap_type == 'file':
        safe = resolve_safe_video_file(cap_path)
        if not safe:
            return jsonify({"error": "无效的视频路径"}), 400
        cap_path = safe

    try:
        # 转换坐标点
        src_points = np.array([[point['x'], point['y']] for point in src_points], dtype=np.float32)

        # 转换危险区域
        danger_zones_np = [np.array(zone, dtype=np.float32) for zone in danger_zones] if danger_zones else []

        cap = Camera()
        cap.setCap(cap_type, cap_path)
        if not cap.getCap().isOpened():
            return jsonify({"error": "无法打开视频源"}), 400

        model_path = Config.DEFAULT_SMART_MODEL_PATH
        if not os.path.exists(model_path):
            return jsonify({"error": "模型文件不存在"}), 400

        # 初始化规则引擎
        rule_engine = RuleEngine()
        if danger_zones_np:
            rule_engine.add_rule(WorkerInDangerZoneRule(danger_zones_np))
        rule_engine.add_rule(VehicleSpeedingRule(Config.VEHICLE_SPEED_LIMIT))
        rule_engine.add_rule(VehicleWorkerProximityRule(Config.MIN_VEHICLE_WORKER_DISTANCE))

        # 初始化AI推理引擎（可选）；优先环境变量 DEEPSEEK_API_KEY，避免密钥写进代码库
        reasoning_engine = None
        deepseek_key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip() or (
            getattr(Config, "DEEPSEEK_API_KEY", "") or ""
        ).strip()
        if enable_ai and deepseek_key:
            deepseek_client = DeepSeekClient(
                deepseek_key,
                base_url=Config.LLM_BASE_URL,
                provider=Config.LLM_PROVIDER,
            )
            reasoning_engine = ReasoningEngine(
                deepseek_client,
                system_prompt=Config.LLM_SYSTEM_PROMPT,
                model_name=Config.LLM_MODEL,
                temperature=Config.LLM_TEMPERATURE,
                max_tokens=Config.LLM_MAX_TOKENS,
                timeout=Config.LLM_TIMEOUT,
            )
        elif enable_ai and not deepseek_key:
            print(
                "[Smart] 已请求启用 DeepSeek(enable_ai=true)，但未设置 DEEPSEEK_API_KEY（环境变量或 Config），推理引擎未创建"
            )

        # 初始化智能监控服务
        with id_lock:
            global current_service_id
            current_service_id += 1
            service_id = current_service_id

            service = SmartMonitoringService(
                model_path=model_path,
                src_points=src_points,
                cap=cap.getCap(),
                rule_engine=rule_engine,
                reasoning_engine=reasoning_engine,
                ai_requested=enable_ai,
                hot_zone=danger_zones_np[0] if danger_zones_np else None,
                stay_threshold=Config.STAY_THRESHOLD,
                loop_file=(cap_type == 'file'),
                cap_type=cap_type,
            )

            # 启动服务线程
            t = threading.Thread(target=service.start)
            t.daemon = True
            t.start()

            smart_services[service_id] = {"service": service, "thread": t}
            print(f"[DEBUG] 服务启动成功，服务ID: {service_id}, 服务实例: {service}")
            print(f"[DEBUG] 当前 smart_services 字典: {list(smart_services.keys())}")
            return jsonify({
                "service_id": service_id,
                "ai_enabled": reasoning_engine is not None,
                "ai_requested": enable_ai,
                "deepseek_key_configured": bool(deepseek_key),
            }), 200

    except Exception as e:
        print("[ERROR]", str(e))
        return jsonify({"error": str(e)}), 500


# 路由：获取原始帧
@smart_api_bp.route('/getRowFrame/<int:service_id>', methods=['GET'])
@with_service
def get_row_frame(service):
    return send_frame_response(service.get_row_frame())


# 路由：获取处理后的帧
@smart_api_bp.route('/getProcessedFrame/<int:service_id>', methods=['GET'])
@with_service
def get_processed_frame(service):
    return send_frame_response(service.get_processed_frame())


# 路由：获取鸟瞰图帧
@smart_api_bp.route('/getBirdViewFrame/<int:service_id>', methods=['GET'])
@with_service
def get_bird_view_frame(service):
    return send_frame_response(service.get_birdView_frame())


# 路由：获取统计信息
@smart_api_bp.route('/getStatistics/<int:service_id>', methods=['GET'])
@with_service
def get_statistics(service):
    return jsonify({"statistics": service.get_statistics()}), 200


# 路由：获取最新告警
@smart_api_bp.route('/getAlerts/<int:service_id>', methods=['GET'])
@with_service
def get_alerts(service):
    max_count = request.args.get('max_count', 10, type=int)
    alerts = service.get_latest_alerts(max_count)
    live_status = service.get_live_monitor_status()
    payload = json.dumps(
        {"alerts": alerts, "live_status": live_status},
        ensure_ascii=False,
        default=str,
    )
    return Response(payload, mimetype="application/json; charset=utf-8"), 200


# 路由：获取最新推理结果
@smart_api_bp.route('/getDecision/<int:service_id>', methods=['GET'])
@with_service
def get_decision(service):
    return jsonify({"decision": service.get_latest_decision()}), 200


# 路由：获取活动规则列表
@smart_api_bp.route('/getRules/<int:service_id>', methods=['GET'])
@with_service
def get_rules(service):
    rules = service.rule_engine.get_active_rules()
    return jsonify({"rules": rules}), 200


# 路由：列出所有服务
@smart_api_bp.route('/listServices', methods=['GET'])
def list_services():
    return jsonify({"services": list(smart_services.keys())}), 200


# 路由：停止并释放服务
@smart_api_bp.route('/release/<int:service_id>', methods=['POST'])
def release_service(service_id):
    with thread_lock:
        if service_id not in smart_services:
            return jsonify({"error": "Service not found"}), 400
        service_info = smart_services.pop(service_id)
        service_info['service'].stop()
        service_info['service'].release()
        service_info['thread'].join(timeout=5)

    return jsonify({"success": True}), 200
