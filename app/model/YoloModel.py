import cv2
import time
import numpy as np
import torch
from ultralytics import YOLO
from collections import defaultdict
from app.config.config import Config


def _infer_device_and_half():
    """按配置与硬件选择 device；半精度仅用于 NVIDIA CUDA。"""
    dev = getattr(Config, "YOLO_DEVICE", "auto")
    if dev == "auto":
        if torch.cuda.is_available():
            dev = 0
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            dev = "mps"
        else:
            dev = "cpu"
    use_half = bool(getattr(Config, "YOLO_HALF", True)) and dev != "cpu" and dev != "mps"
    return dev, use_half


class YoloModel:
    def __init__(self, model_path,
                 src_points,
                 hot_zone,
                 stay_threshold: int,
                 traffic_flow: bool,
                 num_lanes: int,
                 dst_points=np.array([[100, 0], [400, 0], [100, 800], [400, 800]], dtype=np.float32)):
        """
        Initialize the YoloModel class.

        Args:
            model_path (str): Path to the YOLO model.
            src_points (ndarray): 4 points for perspective transformation from original to bird's-eye view.
            hot_zone (ndarray, optional): Polygon coordinates for a special zone (e.g., no-parking zone).
            stay_threshold (int): Time (in seconds) after which a vehicle is considered as staying too long in hot zone.
            traffic_flow (bool): Whether to enable traffic flow counting (crossing middle line).
            num_lanes (int): Number of lanes to draw in the bird’s-eye view.
            dst_points (ndarray): Destination points for perspective transformation (bird’s-eye view).
        """
        self._model_path = model_path
        self._model = None  # 延迟加载，避免在 HTTP 请求线程里卡住
        self.src_points = src_points
        self.dst_points = dst_points
        self.num_lanes = num_lanes
        self.M = cv2.getPerspectiveTransform(src_points, dst_points)

        # Track history for drawing paths
        self.track_history = defaultdict(list)

        # Vehicle counting
        self.vehicle_count = 0
        self.category_count = defaultdict(int)
        self.seen_track_ids = set()

        # Hot zone monitoring
        self.hot_zone = hot_zone
        self.stay_threshold = stay_threshold
        self.entry_time = {}
        self.long_stay_ids = set()

        # Traffic flow counting
        self.traffic_flow = traffic_flow
        self.crossed_ids = set()
        self.crossing_count = 0
        self.track_timestamps = {}
        self.track_speeds = {}
        # 无跟踪模式下，统计区展示「当前帧」车辆数
        self._frame_vehicle_total = 0
        self._frame_category_count = defaultdict(int)
        self.latest_scene_data = {
            "objects": [],
            "vehicles": [],
            "workers": [],
            "equipment": [],
            "danger_zone_objects": [],
            "fast_vehicles": [],
            "abnormal_stays": [],
        }
        self.vehicle_classes = {
            "bicycle", "motorcycle", "car", "bus", "truck", "train", "boat"
        }
        self.worker_classes = {"person"}

    @property
    def model(self):
        if self._model is None:
            self._model = YOLO(self._model_path)
        return self._model

    @staticmethod
    def draw_dashed_line(img, start, end, color, thickness, dash_length, gap_length):
        """
        Draw a dashed line between two points.

        Args:
            img: Image to draw on.
            start: Starting coordinate.
            end: Ending coordinate.
            color: Line color.
            thickness: Line thickness.
            dash_length: Length of each dash.
            gap_length: Length of gap between dashes.
        """
        total_length = int(np.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2))
        num_dashes = total_length // (dash_length + gap_length)

        for i in range(num_dashes):
            dash_start = (
                int(start[0] + (end[0] - start[0]) * (i * (dash_length + gap_length)) / total_length),
                int(start[1] + (end[1] - start[1]) * (i * (dash_length + gap_length)) / total_length)
            )
            dash_end = (
                int(start[0] + (end[0] - start[0]) * ((i * (dash_length + gap_length)) + dash_length) / total_length),
                int(start[1] + (end[1] - start[1]) * ((i * (dash_length + gap_length)) + dash_length) / total_length)
            )
            cv2.line(img, dash_start, dash_end, color, thickness)

    def draw_lane_lines(self, birdView_frame):
        """
        Draw lane lines (solid and dashed) on the bird’s-eye view image.

        Args:
            birdView_frame: Image to draw lane lines on.
        """
        left_line_start = tuple(map(int, self.dst_points[0]))
        left_line_end = tuple(map(int, self.dst_points[2]))
        right_line_start = tuple(map(int, self.dst_points[1]))
        right_line_end = tuple(map(int, self.dst_points[3]))

        # Draw solid boundary lines
        cv2.line(birdView_frame, left_line_start, left_line_end, (255, 255, 255), 2)
        cv2.line(birdView_frame, right_line_start, right_line_end, (255, 255, 255), 2)

        # Draw dashed centerlines for multiple lanes
        for i in range(1, self.num_lanes):
            alpha = i / self.num_lanes
            dashed_start = (
                int(left_line_start[0] + alpha * (right_line_start[0] - left_line_start[0])),
                int(left_line_start[1] + alpha * (right_line_start[1] - left_line_start[1]))
            )
            dashed_end = (
                int(left_line_end[0] + alpha * (right_line_end[0] - left_line_end[0])),
                int(left_line_end[1] + alpha * (right_line_end[1] - left_line_end[1]))
            )
            self.draw_dashed_line(birdView_frame, dashed_start, dashed_end, (255, 255, 255), 2, 20, 10)

    def track(self, frame):
        """
        Perform detection or tracking and annotation on a single frame.

        When Config.ENABLE_TRACKING is False, uses predict() only (faster, no BoT-SORT).

        Returns:
            annotated_frame, frame, birdView_frame
        """
        use_track = bool(getattr(Config, "ENABLE_TRACKING", False))
        frame_timestamp = time.time()
        device, half = _infer_device_and_half()
        infer_kw = dict(
            show=False,
            verbose=False,
            device=device,
            half=half,
            imgsz=int(Config.YOLO_IMGSZ),
            conf=float(Config.YOLO_CONF),
            iou=float(Config.YOLO_IOU),
            max_det=int(Config.YOLO_MAX_DET),
        )
        if use_track:
            results = self.model.track(frame, persist=True, **infer_kw)
        else:
            results = self.model.predict(frame, **infer_kw)

        if not results or not results[0].boxes:
            if not use_track:
                self._frame_vehicle_total = 0
                self._frame_category_count = defaultdict(int)
            return frame, frame, np.zeros((800, 500, 3), dtype=np.uint8)

        boxes = results[0].boxes.xywh.cpu()
        boxes_xyxy = results[0].boxes.xyxy.cpu()
        cls_indices = results[0].boxes.cls.int().cpu().tolist()
        class_names = self.model.names
        n = len(cls_indices)
        if use_track:
            if results[0].boxes.id is not None:
                track_ids = results[0].boxes.id.int().cpu().tolist()
            else:
                track_ids = []
            if len(track_ids) < n:
                track_ids = track_ids + [-(i + 1) for i in range(len(track_ids), n)]
        else:
            track_ids = list(range(n))

        annotated_frame = results[0].plot(labels=False)
        birdView_frame = np.zeros((800, 500, 3), dtype=np.uint8)
        self.draw_lane_lines(birdView_frame)
        scene_objects = []
        vehicles = []
        workers = []
        equipment = []
        danger_zone_objects = []
        fast_vehicles = []

        for box, box_xyxy, track_id, cls_idx in zip(boxes, boxes_xyxy, track_ids, cls_indices):
            class_name = class_names[cls_idx]
            x, y, w, h = box
            world_position = self._transform_point(float(x), float(y))
            in_hot_zone = False

            if use_track:
                if track_id >= 0 and track_id not in self.seen_track_ids:
                    self.seen_track_ids.add(track_id)
                    self.vehicle_count += 1
                    self.category_count[class_name] += 1

                track = self.track_history[track_id]
                track.append((float(x), float(y)))
                if len(track) > Config.TRACK_HISTORY_SIZE:
                    track.pop(0)

                speed_kmh = self._estimate_speed(track_id, world_position, frame_timestamp)

                points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                cv2.polylines(annotated_frame, [points], isClosed=False, color=(230, 230, 230), thickness=10)

                for point in track:
                    src_point = np.array([[[point[0], point[1]]]], dtype=np.float32)
                    dst_point = cv2.perspectiveTransform(src_point, self.M)
                    bx, by = dst_point[0][0]
                    cv2.circle(birdView_frame, (int(bx), int(by)), 5, (0, 255, 0), -1)

                if self.hot_zone is not None:
                    dst_point = cv2.perspectiveTransform(np.array([[[x, y]]], dtype=np.float32), self.M)
                    bx, by = dst_point[0][0]
                    if cv2.pointPolygonTest(self.hot_zone, (int(bx), int(by)), False) >= 0:
                        in_hot_zone = True
                        if track_id not in self.entry_time:
                            self.entry_time[track_id] = time.time()
                        elif time.time() - self.entry_time[track_id] > self.stay_threshold:
                            self.long_stay_ids.add(track_id)
                    elif track_id in self.entry_time:
                        del self.entry_time[track_id]

                if self.traffic_flow:
                    center_y = y
                    prev_positions = self.track_history[track_id][-2:] if len(self.track_history[track_id]) >= 2 else []
                    frame_height = frame.shape[0]
                    middle_line_y = frame_height // 2
                    if len(prev_positions) == 2:
                        prev_y = prev_positions[0][1]
                        curr_y = center_y
                        if (prev_y < middle_line_y <= curr_y) or (prev_y > middle_line_y >= curr_y):
                            if track_id not in self.crossed_ids:
                                self.crossed_ids.add(track_id)
                                self.crossing_count += 1

                if track:
                    src_point = np.array([[[track[-1][0], track[-1][1]]]], dtype=np.float32)
                    dst_point = cv2.perspectiveTransform(src_point, self.M)
                    bx, by = dst_point[0][0]
                    cv2.putText(
                        birdView_frame,
                        f"ID:{int(track_id)}",
                        (int(bx), max(int(by) - 10, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 255),
                        2,
                        cv2.LINE_AA,
                    )

            else:
                speed_kmh = 0.0
                if self.hot_zone is not None:
                    dst_point = cv2.perspectiveTransform(np.array([[[x, y]]], dtype=np.float32), self.M)
                    bx, by = dst_point[0][0]
                    in_hot_zone = cv2.pointPolygonTest(self.hot_zone, (int(bx), int(by)), False) >= 0

            object_data = {
                "track_id": int(track_id),
                "class_name": class_name,
                "bbox_xywh": [float(x), float(y), float(w), float(h)],
                "bbox_xyxy": [float(v) for v in box_xyxy.tolist()],
                "image_position": [float(x), float(y)],
                "position": list(world_position),
                "world_position": list(world_position),
                "speed": float(speed_kmh),
                "in_hot_zone": in_hot_zone,
            }
            scene_objects.append(object_data)

            if class_name in self.worker_classes:
                worker_object = {**object_data, "has_helmet": True}
                workers.append(worker_object)
                if in_hot_zone:
                    danger_zone_objects.append(worker_object)
            elif class_name in self.vehicle_classes:
                vehicles.append(object_data)
                if speed_kmh > 0:
                    fast_vehicles.append(object_data)
                if in_hot_zone:
                    danger_zone_objects.append(object_data)
            else:
                equipment.append(object_data)

            # 框外标注 track_id，与场景 JSON / DeepSeek 文案中的 id 一致（predict 模式下为帧内序号 0,1,…）
            x1, y1, x2, y2 = [int(v) for v in box_xyxy.tolist()]
            cv2.putText(
                annotated_frame,
                f"ID:{int(track_id)}",
                (x1, max(y1 - 8, 14)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.58,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

        if not use_track:
            self._frame_vehicle_total = len(vehicles)
            fc = defaultdict(int)
            for v in vehicles:
                fc[v["class_name"]] += 1
            self._frame_category_count = fc

        self.latest_scene_data = {
            "objects": scene_objects,
            "vehicles": vehicles,
            "workers": workers,
            "equipment": equipment,
            "danger_zone_objects": danger_zone_objects,
            "fast_vehicles": fast_vehicles,
            "abnormal_stays": sorted(self.long_stay_ids) if use_track else [],
        }

        return annotated_frame, frame, birdView_frame

    def _transform_point(self, x, y):
        src_point = np.array([[[x, y]]], dtype=np.float32)
        dst_point = cv2.perspectiveTransform(src_point, self.M)
        bx, by = dst_point[0][0]
        return (
            float(bx / Config.PIXELS_PER_METER),
            float(by / Config.PIXELS_PER_METER),
        )

    def _estimate_speed(self, track_id, world_position, timestamp):
        previous_timestamp = self.track_timestamps.get(track_id)
        previous_position = self.track_history[track_id][-2] if len(self.track_history[track_id]) >= 2 else None
        self.track_timestamps[track_id] = timestamp

        if previous_timestamp is None or previous_position is None:
            self.track_speeds[track_id] = 0.0
            return 0.0

        delta_t = timestamp - previous_timestamp
        if delta_t <= 0:
            return self.track_speeds.get(track_id, 0.0)

        previous_world = self._transform_point(previous_position[0], previous_position[1])
        distance_m = np.sqrt(
            (world_position[0] - previous_world[0]) ** 2 +
            (world_position[1] - previous_world[1]) ** 2
        )
        speed_kmh = (distance_m / delta_t) * 3.6
        self.track_speeds[track_id] = float(speed_kmh)
        return float(speed_kmh)

    def get_scene_data(self):
        return {
            "objects": list(self.latest_scene_data.get("objects", [])),
            "vehicles": list(self.latest_scene_data.get("vehicles", [])),
            "workers": list(self.latest_scene_data.get("workers", [])),
            "equipment": list(self.latest_scene_data.get("equipment", [])),
            "danger_zone_objects": list(self.latest_scene_data.get("danger_zone_objects", [])),
            "fast_vehicles": list(self.latest_scene_data.get("fast_vehicles", [])),
            "abnormal_stays": list(self.latest_scene_data.get("abnormal_stays", [])),
        }

    def get_statistics(self):
        """
        Get current statistics.

        Returns:
            dict: Total vehicles, category counts, long stays, and flow crossing count.
        """
        if not getattr(Config, "ENABLE_TRACKING", False):
            return {
                "total_count": self._frame_vehicle_total,
                "category_count": dict(self._frame_category_count),
                "long_stay_count": 0,
                "crossing_count": 0,
            }
        return {
            "total_count": self.vehicle_count,
            "category_count": self.category_count,
            "long_stay_count": len(self.long_stay_ids),
            "crossing_count": self.crossing_count,
        }

    def reset_statistics(self):
        """
        Reset all statistical counters and trackers.
        """
        self.vehicle_count = 0
        self.category_count = defaultdict(int)
        self.seen_track_ids = set()
        self.entry_time.clear()
        self.long_stay_ids = set()
        self.crossing_count = 0
        self.crossed_ids.clear()
        self.track_timestamps.clear()
        self.track_speeds.clear()
        self._frame_vehicle_total = 0
        self._frame_category_count = defaultdict(int)
        self.latest_scene_data = {
            "objects": [],
            "vehicles": [],
            "workers": [],
            "equipment": [],
            "danger_zone_objects": [],
            "fast_vehicles": [],
            "abnormal_stays": [],
        }

   
