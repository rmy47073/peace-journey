# YOLO 施工道路智能监控系统

基于 `Flask + Vue + Ultralytics YOLO` 的视频监控项目，支持本地视频/网络摄像头接入、实时检测、智能告警与（可选）DeepSeek 风险分析。

## 项目概述

本项目包含两条主要能力线：

- `基础检测服务`：实时画面识别、车辆/人员目标检测、帧流接口。
- `智能监控服务`：规则引擎（如超速、车人过近、危险区）+ 告警历史 + 可选 DeepSeek 推理增强。

核心特点：

- 本地视频与 RTSP 摄像头双输入。
- 前后端分离，前端可直接选取 `videos/` 下素材并预览。
- 采集线程与推理线程解耦，降低卡顿。
- 告警历史静态保存（轮询不消费），支持滚动查看。
- 可切换是否启用目标跟踪（`track`/`predict`）。

## 技术栈

- 后端：`Python`、`Flask`、`OpenCV`、`PyTorch`、`Ultralytics`
- 前端：`Vue 3`、`Vite`、`Axios`、`Vue Router`

## 目录结构（简版）

```text
.
├─app/                    # 后端业务
│  ├─config/              # 配置项（模型、推理参数、DeepSeek、规则阈值）
│  ├─model/               # YOLO 模型封装
│  ├─service/             # 基础检测与智能监控服务
│  ├─ai/                  # DeepSeek 客户端与推理引擎
│  ├─routes.py            # /api 路由
│  └─smart_routes.py      # /smart 路由
├─frontend/               # Vue 前端
├─models/                 # YOLO 权重（*.pt）
├─videos/                 # 本地测试视频
├─requirements.txt        # Python 依赖
└─app.py                  # 后端启动入口
```

## 环境与依赖

建议环境：

- `Python 3.10+`
- `Node.js 18+`（或 20）
- `npm 9+`

Python 依赖（见 `requirements.txt`）：

- `opencv-python`
- `numpy`
- `ultralytics`
- `flask`
- `flask-cors`
- `torch`
- `torchvision`
- `requests`

前端依赖（见 `frontend/package.json`）：

- `vue`
- `vue-router`
- `axios`
- `vite`
- `@vitejs/plugin-vue`

## 如何启动

### 1) 准备模型与视频

1. 将 YOLO 权重文件放到 `models/`（例如 `models/yolov10n.pt`）。
2. 将测试视频放到 `videos/`（可在前端直接选择并分析）。

### 2) 启动后端

```bash
# 建议在项目根目录
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# 启动 Flask
python app.py
```

默认监听：`http://localhost:5000`

### 3) 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认访问：`http://localhost:3000`

前端开发代理已配置到后端：

- `/api` -> `http://localhost:5000`
- `/smart` -> `http://localhost:5000`

## DeepSeek（可选）

如果需要 AI 推理增强，请配置环境变量：

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="your_key_here"
```

然后重启后端。未配置时，系统仍可运行规则引擎，但不会调用 DeepSeek。

## 常用配置位置

主要配置在 `app/config/config.py`：

- 推理性能：`PROCESS_EVERY_N_FRAMES`、`YOLO_IMGSZ`、`MAX_FRAME_WIDTH`
- 跟踪开关：`ENABLE_TRACKING`
- 视频节流：`SYNC_VIDEO_FILE_TO_REALTIME`
- 告警历史：`ALERT_HISTORY_MAX`
- DeepSeek：`DEEPSEEK_ENABLED`、`LLM_*`

