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
    # False：只用 YOLO detect（predict），不做 BoT-SORT 跟踪，更流畅；画面无轨迹尾迹、无稳定 id
    # True：track() + 轨迹线 + 车速/越线/累计计数等（更耗性能）
    ENABLE_TRACKING = False
    TRACK_HISTORY_SIZE = 22
    PIXELS_PER_METER = 25.0
    REASONING_QUEUE_SIZE = 8
    # 告警历史最大条数（只追加，GET 不消费；超出丢弃最旧）
    ALERT_HISTORY_MAX = 200
    # 每隔若干秒刷新运行状态快照，仅用于接口 live_status，不写入告警历史（0 关闭）
    ALERT_HEARTBEAT_SECONDS = 5.0
    FRAME_QUEUE_SIZE = 3
    # 每 N 帧做一次完整推理；轻薄本建议 5～8，有独显可降到 2～4
    PROCESS_EVERY_N_FRAMES = 7
    ENABLE_FRAME_RESIZE = True
    # 解码后限制宽度再送 YOLO；越小越快（720 适合核显/CPU，960 更清但更卡）
    MAX_FRAME_WIDTH = 720
    # 推理输入边长：960 在 CPU 上极慢；512～640 更适合轻薄本，精度略降
    YOLO_IMGSZ = 512
    YOLO_CONF = 0.22
    YOLO_IOU = 0.5
    # 单帧最大检测数，过大拖慢 NMS 与轨迹绘制
    YOLO_MAX_DET = 50
    # auto：优先 NVIDIA CUDA，其次 Apple MPS，否则 CPU
    YOLO_DEVICE = "auto"
    # 仅在 NVIDIA GPU 上生效（FP16 加速）；CPU/MPS 会自动关闭
    YOLO_HALF = True
    JPEG_QUALITY = 58
    # 本地文件源：按视频 FPS 节流采集，避免「像快进」；RTSP 不生效
    SYNC_VIDEO_FILE_TO_REALTIME = True
    # 元数据无 FPS 或异常时的假定帧率
    VIDEO_FILE_FALLBACK_FPS = 25.0
    # False：只要启用 DeepSeek 且事件触发就会调用大模型（由 EventTrigger 控频）
    # True：恢复旧逻辑，仅多条/高级别告警时才调用 API（省费用）
    LLM_ONLY_ON_HEAVY_ALERTS = False

    # DeepSeek配置（可选）；推荐用环境变量 DEEPSEEK_API_KEY，勿把真密钥提交到 Git
    # 若接口返回 HTTP 402 Insufficient Balance，需在 https://platform.deepseek.com 充值
    DEEPSEEK_API_KEY = "sk-d24a9c0b7c9c4c2c8f035b2b89609d74"
    # True：默认启用 AI 推理；智能监控请求里未传 enable_ai 时按此项。前端勾选「启用 DeepSeek」会传 enable_ai=true
    DEEPSEEK_ENABLED = True
    LLM_PROVIDER = "deepseek_api"  # deepseek_api / openai_compatible / ollama
    LLM_BASE_URL = "https://api.deepseek.com/v1"
    LLM_MODEL = "deepseek-chat"
    LLM_TIMEOUT = 30
    LLM_TEMPERATURE = 0.3
    LLM_MAX_TOKENS = 1200
    # DeepSeek 调用最小间隔（秒），越小「最新告警」里越常出现 AI 内容
    LLM_FIXED_INTERVAL_SECONDS = 1.2
    LLM_FORCE_TRIGGER_RISK_LEVELS = {"high", "critical"}
    LLM_MIN_ALERT_COUNT = 1
    LLM_SCENE_CHANGE_THRESHOLD = 1
    LLM_ENABLE_FIXED_INTERVAL = True
    LLM_SYSTEM_PROMPT = (
        "你是一个拥有20年经验的施工现场安全监理专家。"
        "请根据实时监控结构化数据判断是否存在安全隐患。"
        "如果存在，请说明原因，给出预警等级（low/medium/high/critical）和处理建议。"
        "输出必须为JSON。"
    )

    # 安全规则配置
    VEHICLE_SPEED_LIMIT = 20.0  # km/h
    MIN_VEHICLE_WORKER_DISTANCE = 3.0  # 米
    STAY_THRESHOLD = 5  # 秒
