# 施工道路智能监测预警系统

基于YOLO目标检测、规则引擎和大语言模型(DeepSeek)的施工道路实时监测和预警系统。

## 系统架构

```
施工道路智能监测预警系统
├── 感知层 (Perception Layer)
│   ├── YOLO目标检测与跟踪
│   ├── 透视变换与鸟瞰图
│   └── 多目标轨迹追踪
│
├── 决策层 (Decision Layer)
│   ├── 规则引擎 (Rule Engine)
│   │   ├── 危险区域入侵检测
│   │   ├── 车辆超速检测
│   │   ├── 安全装备检测
│   │   └── 车辆-工人距离检测
│   │
│   └── AI推理引擎 (Reasoning Engine)
│       ├── DeepSeek大模型集成
│       ├── 场景理解与分析
│       └── 智能决策建议
│
└── 应用层 (Application Layer)
    ├── 实时视频流处理
    ├── 告警管理与推送
    ├── 统计分析与可视化
    └── RESTful API接口
```

## 核心功能

### 1. 目标检测与跟踪
- 基于YOLOv11的实时目标检测
- 多目标持续跟踪
- 透视变换生成鸟瞰图
- 轨迹可视化

### 2. 规则引擎
- **危险区域监控**: 检测工人进入危险区域
- **车辆超速检测**: 监控车辆速度，超速告警
- **安全装备检测**: 检查工人是否佩戴安全帽等装备
- **距离监控**: 检测车辆与工人距离过近情况

### 3. AI智能推理
- 集成DeepSeek大语言模型
- 复杂场景智能分析
- 类人推理决策
- 自动生成安全建议

### 4. 实时预警
- 多级告警机制 (low/medium/high/critical)
- 实时告警推送
- 告警历史记录
- 决策建议输出

## 项目结构

```
yolo-track-master/
├── app/
│   ├── __init__.py
│   ├── routes.py                    # 原有API路由
│   ├── smart_routes.py              # 智能监控API路由 (新增)
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py                # 配置文件 (已更新)
│   │
│   ├── model/
│   │   ├── __init__.py
│   │   └── YoloModel.py             # YOLO检测模型
│   │
│   ├── service/
│   │   ├── __init__.py
│   │   ├── YoloService.py           # 原有YOLO服务
│   │   └── SmartMonitoringService.py # 智能监控服务 (新增)
│   │
│   ├── alert/                        # 告警模块 (新增)
│   │   ├── __init__.py
│   │   └── rule_engine.py           # 规则引擎
│   │
│   ├── ai/                           # AI模块 (新增)
│   │   ├── __init__.py
│   │   ├── deepseek_client.py       # DeepSeek客户端
│   │   └── reasoning_engine.py      # 推理决策引擎
│   │
│   └── util/
│       ├── __init__.py
│       └── Camera.py                # 摄像头工具
│
├── models/
│   └── yolo11n.pt                   # YOLO模型文件
│
├── videos/                          # 测试视频
├── frontend/                        # 前端界面
├── app.py                           # 应用入口
├── requirements.txt                 # 依赖包 (已更新)
└── README_SMART.md                  # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置系统

编辑 `app/config/config.py`:

```python
class Config:
    # DeepSeek配置（可选）
    DEEPSEEK_API_KEY = "your-api-key-here"  # 填入DeepSeek API密钥
    DEEPSEEK_ENABLED = True  # 启用AI推理
    
    # 安全规则配置
    VEHICLE_SPEED_LIMIT = 20.0  # 车辆速度限制 (km/h)
    MIN_VEHICLE_WORKER_DISTANCE = 3.0  # 最小安全距离 (米)
    STAY_THRESHOLD = 5  # 停留时间阈值 (秒)
```

### 3. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动

## API接口

### 启动智能监控

```http
POST /smart/start
Content-Type: application/json

{
  "src_points": [
    {"x": 100, "y": 200},
    {"x": 500, "y": 200},
    {"x": 100, "y": 600},
    {"x": 500, "y": 600}
  ],
  "cap_type": "video",
  "cap_path": "./videos/test.mp4",
  "danger_zones": [
    [[150, 250], [450, 250], [450, 550], [150, 550]]
  ],
  "enable_ai": true
}
```

响应:
```json
{
  "service_id": 1,
  "ai_enabled": true
}
```

### 获取实时告警

```http
GET /smart/getAlerts/{service_id}?max_count=10
```

响应:
```json
{
  "alerts": [
    {
      "timestamp": 1234567890.123,
      "rules_result": {
        "alerts": [
          {
            "rule_id": "R001",
            "type": "worker_in_danger_zone",
            "level": "critical",
            "message": "工人 ID:5 进入危险区域",
            "object_id": 5
          }
        ],
        "risk_level": "critical"
      },
      "decision": {
        "ai_analysis": {
          "risk_level": "critical",
          "risks": ["工人在危险区域内", "附近有移动车辆"],
          "suggestions": ["立即疏散工人", "停止车辆作业"],
          "immediate_actions": ["发出紧急警报"],
          "reasoning": "检测到工人进入施工危险区域..."
        },
        "final_decision": {...},
        "confidence": 0.9
      }
    }
  ]
}
```

### 获取统计信息

```http
GET /smart/getStatistics/{service_id}
```

### 获取处理后的视频帧

```http
GET /smart/getProcessedFrame/{service_id}
GET /smart/getBirdViewFrame/{service_id}
GET /smart/getRowFrame/{service_id}
```

### 获取活动规则

```http
GET /smart/getRules/{service_id}
```

### 停止服务

```http
POST /smart/release/{service_id}
```

## 规则引擎详解

### 内置规则

1. **WorkerInDangerZoneRule (R001)**
   - 级别: Critical
   - 检测工人是否进入预定义的危险区域

2. **VehicleSpeedingRule (R002)**
   - 级别: High
   - 检测车辆是否超过速度限制

3. **NoSafetyEquipmentRule (R003)**
   - 级别: High
   - 检测工人是否佩戴安全装备

4. **VehicleWorkerProximityRule (R004)**
   - 级别: Critical
   - 检测车辆与工人距离是否过近

### 自定义规则

继承 `SafetyRule` 类创建自定义规则:

```python
from app.alert.rule_engine import SafetyRule

class CustomRule(SafetyRule):
    def __init__(self):
        super().__init__("R005", "自定义规则", "high")
    
    def check(self, scene_data: Dict) -> List[Dict]:
        alerts = []
        # 实现检测逻辑
        return alerts
```

## AI推理引擎

### DeepSeek集成

系统集成DeepSeek大语言模型进行智能场景分析:

1. **场景理解**: 分析检测到的对象、位置、运动状态
2. **风险评估**: 综合多种因素评估整体风险
3. **决策建议**: 生成具体的安全建议和行动方案
4. **推理解释**: 提供决策的推理过程

### 工作流程

```
场景数据 → 规则引擎评估 → AI推理引擎分析 → 综合决策输出
```

- 简单场景: 仅使用规则引擎 (快速响应)
- 复杂场景: 规则引擎 + AI推理 (深度分析)

## 技术栈

- **深度学习**: YOLOv11 (Ultralytics)
- **计算机视觉**: OpenCV
- **大语言模型**: DeepSeek API
- **Web框架**: Flask
- **深度学习框架**: PyTorch

## 性能优化

- 多线程处理，视频流与推理分离
- 队列缓冲机制，防止帧丢失
- 规则引擎快速响应，AI按需调用
- 告警去重和聚合

## 扩展方向

1. **检测能力扩展**
   - 增加更多目标类别 (工人、设备、材料等)
   - 姿态估计 (检测工人动作)
   - 安全装备细粒度识别

2. **规则引擎增强**
   - 时序规则 (连续违规检测)
   - 复合规则 (多条件组合)
   - 动态规则配置

3. **AI能力提升**
   - 本地部署DeepSeek模型
   - 多模态分析 (图像+文本)
   - 预测性分析

4. **系统集成**
   - 告警推送 (短信、邮件、钉钉)
   - 数据库持久化
   - 大屏可视化
   - 移动端APP

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或Pull Request。
