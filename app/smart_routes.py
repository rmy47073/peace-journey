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
from flask import request, Blueprint, jsonify, Response


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
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            return jsonify({"error": "Failed to encode frame"}), 500
        frame = jpeg.tobytes()

    if not isinstance(frame, bytes):
        return jsonify({"error": "Invalid frame format"}), 500

    return Response(frame, mimetype='image/jpeg')


# 路由：获取视频文件列表
@smart_api_bp.route('/fileList', methods=['GET'])
def fileList():
    folder_path = "./videos"
    file_list = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    return jsonify({"file_list": file_list}), 200


# 路由：获取单帧
@smart_api_bp.route('/getOneFrame', methods=['POST'])
def get_one_frame():
    cap_type = request.json.get('cap_type')
    cap_path = request.json.get('cap_path')
    cap = Camera()
    cap.setCap(cap_type, cap_path)
    if not cap.getCap().isOpened():
        return jsonify({"error": "无法打开视频源"}), 400

    ret, frame = cap.getCap().read()
    cap.getCap().release()

    if not ret:
        return jsonify({"error": "Failed to capture frame"}), 500

    ret, jpeg = cv2.imencode('.jpg', frame)
    if not ret:
        return jsonify({"error": "Failed to encode frame"}), 500
    frame_bytes = jpeg.tobytes()

    return send_frame_response(frame_bytes)


# 路由：启动智能监控服务
@smart_api_bp.route('/start', methods=['POST'])
def start_smart_service():
    if not request.json or 'src_points' not in request.json:
        return jsonify({"error": "必须提供src_points参数"}), 400

    src_points = request.json.get('src_points')
    cap_type = request.json.get('cap_type')
    cap_path = request.json.get('cap_path')
    danger_zones = request.json.get('danger_zones', [])  # 危险区域配置
    enable_ai = request.json.get('enable_ai', Config.DEEPSEEK_ENABLED)

    # 参数验证
    if not src_points or len(src_points) < 4:
        return jsonify({"error": "至少需要4个源点坐标"}), 400
    if not cap_type or not cap_path:
        return jsonify({"error": "必须提供capture类型和路径"}), 400

    try:
        # 转换坐标点
        src_points = np.array([[point['x'], point['y']] for point in src_points], dtype=np.float32)

        # 转换危险区域
        danger_zones_np = [np.array(zone, dtype=np.float32) for zone in danger_zones] if danger_zones else []

        cap = Camera()
        cap.setCap(cap_type, cap_path)
        if not cap.getCap().isOpened():
            return jsonify({"error": "无法打开视频源"}), 400

        model_path = "models/yolo11n.pt"
        if not os.path.exists(model_path):
            return jsonify({"error": "模型文件不存在"}), 400

        # 初始化规则引擎
        rule_engine = RuleEngine()
        if danger_zones_np:
            rule_engine.add_rule(WorkerInDangerZoneRule(danger_zones_np))
        rule_engine.add_rule(VehicleSpeedingRule(Config.VEHICLE_SPEED_LIMIT))
        rule_engine.add_rule(VehicleWorkerProximityRule(Config.MIN_VEHICLE_WORKER_DISTANCE))

        # 初始化AI推理引擎（可选）
        reasoning_engine = None
        if enable_ai and Config.DEEPSEEK_API_KEY:
            deepseek_client = DeepSeekClient(Config.DEEPSEEK_API_KEY)
            reasoning_engine = ReasoningEngine(deepseek_client)

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
                hot_zone=danger_zones_np[0] if danger_zones_np else None,
                stay_threshold=Config.STAY_THRESHOLD
            )

            # 启动服务线程
            t = threading.Thread(target=service.start)
            t.daemon = True
            t.start()

            smart_services[service_id] = {"service": service, "thread": t}
            return jsonify({
                "service_id": service_id,
                "ai_enabled": reasoning_engine is not None
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
    return jsonify({"alerts": alerts}), 200


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
