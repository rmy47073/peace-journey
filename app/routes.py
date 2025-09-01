import os
import cv2
import threading
import numpy as np
from functools import wraps
from app.util.Camera import Camera
from app.service.YoloService import YoloService
from flask import request, Blueprint, jsonify, Response


# Decorator for routes that require a running service
def with_service(func):
    @wraps(func)
    def wrapper(service_id, *args, **kwargs):
        try:
            service_info = yolo_services.get(service_id)
            if not service_info or 'service' not in service_info:
                return jsonify({"error": "Service not found"}), 400
            service = service_info['service']
            return func(service, *args, **kwargs)
        except Exception as e:
            return jsonify({"error": f"Internal error: {str(e)}"}), 500
    return wrapper


# Create a Blueprint for API routes
api_bp = Blueprint('api', __name__)

# Store multiple YoloService instances
yolo_services = {}

# Service ID management
current_service_id = 0
id_lock = threading.Lock()
thread_lock = threading.Lock()


# Utility: send frame as image/jpeg response
def send_frame_response(frame):
    if frame is None:
        return jsonify({"error": "No frame available"}), 400

    # Convert NumPy array to JPEG
    if isinstance(frame, np.ndarray):
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            return jsonify({"error": "Failed to encode frame"}), 500
        frame = jpeg.tobytes()

    # Ensure frame is in bytes
    if not isinstance(frame, bytes):
        return jsonify({"error": "Invalid frame format"}), 500

    return Response(frame, mimetype='image/jpeg')


# Route: Get list of video files in the ./videos directory
@api_bp.route('/fileList', methods=['GET'])
def fileList():
    folder_path = "./videos"
    file_list = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    return jsonify({"file_list": file_list}), 200


# Route: Capture and return a single frame from camera or video
@api_bp.route('/getOneFrame', methods=['POST'])
def get_one_frame():
    cap_type = request.json.get('cap_type')
    cap_path = request.json.get('cap_path')
    cap = Camera()
    cap.setCap(cap_type, cap_path)
    if not cap.getCap().isOpened():
        print(f"[DEBUG] Failed to open {cap_type} source at {cap_path}")
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


# Route: Start a YoloService instance with specified source points and capture source
@api_bp.route('/start', methods=['POST'])
def start_service():
    if not request.json or 'src_points' not in request.json:
        return jsonify({"error": "必须提供src_points参数"}), 400
    
    src_points = request.json.get('src_points')
    cap_type = request.json.get('cap_type')
    cap_path = request.json.get('cap_path')

    # 参数验证
    if not src_points or len(src_points) < 4:
        return jsonify({"error": "至少需要4个源点坐标"}), 400
    if not cap_type or not cap_path:
        return jsonify({"error": "必须提供capture类型和路径"}), 400

    try:
        # 转换坐标点为numpy数组
        src_points = np.array([[point['x'], point['y']] for point in src_points], dtype=np.float32)
        print("[DEBUG] Src points shape:", src_points.shape)  # 应为(4,2)

        cap = Camera()
        cap.setCap(cap_type, cap_path)
        if not cap.getCap().isOpened():
            return jsonify({"error": "无法打开视频源"}), 400

        model_path = "models/yolov10n.pt"  # 修正模型文件名
        if not os.path.exists(model_path):
            return jsonify({"error": "模型文件不存在"}), 400

        # 初始化服务
        with id_lock:
            global current_service_id
            current_service_id += 1
            service_id = current_service_id
            service = YoloService(model_path, src_points, cap.getCap())
            
            # 启动服务线程
            t = threading.Thread(target=service.start)
            t.daemon = True
            t.start()
            
            yolo_services[service_id] = {"service": service, "thread": t}
            return jsonify({"service_id": service_id}), 200

    except Exception as e:
        print("[ERROR]", str(e))
        return jsonify({"error": str(e)}), 500


# Route: Get raw (unprocessed) frame from a running service
@api_bp.route('/getRowFrame/<int:service_id>', methods=['GET'])
@with_service
def get_row_frame(service):
    return send_frame_response(service.get_row_frame())

# 获取所有活跃服务ID
@api_bp.route('/listServices', methods=['GET'])
def list_services():
    return jsonify({"services": list(yolo_services.keys())}), 200

# 更新服务参数
@api_bp.route('/updateConfig/<int:service_id>', methods=['POST'])
@with_service
def update_config(service, service_id):
    new_hot_zone = request.json.get('hot_zone')
    if new_hot_zone:
        service.model.hot_zone = np.array(new_hot_zone)
    return jsonify({"success": True}), 200

# 添加对undefined的处理
@api_bp.route('/getRowFrame/undefined', methods=['GET'])
def handle_undefined_service():
    return jsonify({"error": "Service ID is undefined"}), 400


# Route: Get processed detection frame from a running service
@api_bp.route('/getProcessedFrame/<int:service_id>', methods=['GET'])
@with_service
def get_processed_frame(service):
    return send_frame_response(service.get_processed_frame())


# Route: Get bird's-eye view frame from a running service
@api_bp.route('/getBirdViewFrame/<int:service_id>', methods=['GET'])
@with_service
def get_bird_view_frame(service):
    return send_frame_response(service.get_birdView_frame())


# Route: Stop and release a YoloService instance
@api_bp.route('/release/<int:service_id>', methods=['GET'])
def release_service(service_id):
    with thread_lock:
        if service_id not in yolo_services:
            return jsonify({"error": "Service not found"}), 400
        service = yolo_services.pop(service_id)
        service['service'].release()
        service['thread'].join()

    return jsonify({"success": True}), 200


# Route: Get runtime statistics of a service
@api_bp.route('/getStatistics/<int:service_id>', methods=['POST'])
def get_statistics(service_id):
    # 修改前
    service = yolo_services[service_id]['service']
    
    # 修改后 - 添加字典存在性检查
    if service_id not in yolo_services:
        return {'error': f'Service {service_id} not found'}, 404
    service = yolo_services[service_id]['service']
    if service is None:
        return jsonify({"error": "Service not started"}), 400
    return jsonify({"statistics": service.get_statistics()}), 200
