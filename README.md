# 🚗 Intelligent Vehicle Monitoring System

> A Flask-powered real-time vehicle detection and monitoring system with YOLO, multithreaded processing, perspective transformation, and web API support.

## 📌 Features

- 🔍 **Real-time Vehicle Detection** using YOLO
- 🎯 **Perspective Transformation** with customizable bird’s-eye view
- 🔧 **Modular Service Management** (multi-service support via `service_id`)
- 📊 **Vehicle Statistics** (e.g. counts, movement)
- 🧵 **Multi-threaded Processing** to ensure responsive UI and real-time performance
- 🌐 **RESTful API** for frontend/backend integration
- 🎥 **Support for both Local Video & Live Camera Streams**
---

## 🗂️ Project Structure

```
.
├── README.md
├── app
│   ├── __init__.py
│   ├── routes.py
│   ├── config
│   │   ├── __init__.py
│   │   └── config.py
│   ├── model
│   │   ├── YoloModel.py
│   │   └── __init__.py
│   ├── service
│   │   ├── YoloService.py
│   │   └── __init__.py
│   └── util
│       ├── Camera.py
│       └── __init__.py
├── app.py
├── models
│   └── yolo11n.pt
├── requirements.txt
├── test
│   └── YoloModelTest.py
└── videos
    ├── test.mp4
    └── test1.mp4
```



---

## 🚀 Quick Start

### 1. Install Dependencies

```commandline
pip install -r requirements.txt
```

### 2. Prepare YOLO Model
Download YOLOv10 model file and place it at:
```
./models/*.pt
```

You can get it from [YOLO official website](https://github.com/ultralytics/ultralytics) or convert a .pt file via training.

### 3. Run the Server

```commandline
python app.py
```
flask server will run on `http://localhost:5000`

---

## 🔮 Future Improvements
While the current system already supports real-time vehicle detection, multithreaded backend services,
and flexible video source handling, there are several exciting directions for future enhancements:

- ### 🚀 Performance Optimization
 Improves the backend service responsiveness
  and reduces processing latency under high-concurrency or long-duration tasks,
  especially when dealing with high-resolution streams.

- ### 📊 Richer Statistics & Analytics
 Add advanced metrics such as vehicle counting by type, speed estimation,
  and violation detection (e.g., running red lights, wrong-way driving)
  to better serve traffic management and security scenarios.

- ### 🧠 Smarter Lane Detection
 Introduces a more robust and accurate lane line recognition module that integrates seamlessly with vehicle tracking,
 even in complex environments with occlusions or poor lighting.

- ### 🌐 Web UI Enhancement
 Develops a user-friendly web dashboard for visualizing statistics,
 watching processed video streams, and managing uploaded footage.

- ### 🤝 Third-Party Integration
 Explore integration with GIS systems, traffic control platforms, or even cloud-based video analysis tools.

---

Stay tuned—this project has wheels, and it’s just starting to roll. 🚗💨