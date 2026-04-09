DISPLAY_OUTPUT = True
IP_CAMERA_URL = 'rtsp://admin:12345678.@192.168.1.65:554/Streaming/Channels/101'


class Config:
    DEBUG = True
    PORT = 5000
    API_PREFIX = "/api"
    SMART_API_PREFIX = "/smart"

    # 模型与推理配置
    DEFAULT_MODEL_PATH = "models/yolov10n.pt"
    DEFAULT_SMART_MODEL_PATH = "models/yolov10n.pt"
    TRACK_HISTORY_SIZE = 30
    PIXELS_PER_METER = 25.0

    # DeepSeek配置（可选）
    DEEPSEEK_API_KEY = ""  # 填入你的DeepSeek API密钥
    DEEPSEEK_ENABLED = False  # 是否启用DeepSeek AI推理

    # 安全规则配置
    VEHICLE_SPEED_LIMIT = 20.0  # km/h
    MIN_VEHICLE_WORKER_DISTANCE = 3.0  # 米
    STAY_THRESHOLD = 5  # 秒
