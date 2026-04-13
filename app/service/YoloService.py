import queue
import time
import numpy as np
import cv2
from threading import Lock, Thread
from typing import Optional

from app.model.YoloModel import YoloModel
from app.config.config import Config
from app.util.video_fs import file_frame_period_seconds


class YoloService:
    """
    A service wrapper for the YoloModel, responsible for managing video capture,
    model inference, and returning various frame outputs to upstream consumers.
    采集与推理分线程：读流不被 track() 阻塞，检测侧只消费队列中最新帧。
    """

    def __init__(
        self,
        model_path,
        src_points,
        cap,
        hot_zone=None,
        stay_threshold=5,
        traffic_flow=False,
        num_lanes=2,
        loop_file=False,
        cap_type: str = "file",
    ):
        self.model = YoloModel(model_path, src_points, hot_zone, stay_threshold, traffic_flow, num_lanes)
        self.cap = cap
        self.loop_file = loop_file
        self.cap_type = cap_type
        self._file_frame_period = (
            file_frame_period_seconds(cap) if cap_type == "file" else 0.0
        )
        self.frame_lock = Lock()
        self.running = False
        self._last_row = None
        self._last_processed = None
        self._last_bird = None
        self.infer_queue: queue.Queue = queue.Queue(maxsize=1)
        self._capture_thread: Optional[Thread] = None
        self._infer_thread: Optional[Thread] = None

    @staticmethod
    def _clone_frame(frame):
        return frame.copy() if isinstance(frame, np.ndarray) else frame

    def _resize_if_needed(self, frame):
        if not Config.ENABLE_FRAME_RESIZE or frame is None:
            return frame
        height, width = frame.shape[:2]
        if width <= Config.MAX_FRAME_WIDTH:
            return frame
        scale = Config.MAX_FRAME_WIDTH / float(width)
        new_size = (int(width * scale), int(height * scale))
        return cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)

    def _enqueue_infer(self, frame: np.ndarray) -> None:
        item = self._clone_frame(frame)
        try:
            self.infer_queue.put_nowait(item)
        except queue.Full:
            try:
                self.infer_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.infer_queue.put_nowait(item)
            except queue.Full:
                pass

    def _signal_infer_shutdown(self) -> None:
        try:
            self.infer_queue.put_nowait(None)
        except queue.Full:
            try:
                self.infer_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.infer_queue.put_nowait(None)
            except queue.Full:
                pass

    def _last_processed_is_none(self) -> bool:
        with self.frame_lock:
            return self._last_processed is None

    def _capture_loop(self) -> None:
        n = max(Config.PROCESS_EVERY_N_FRAMES, 1)
        frame_count = 0
        try:
            while self.running:
                t0 = time.perf_counter()
                ret, frame = self.cap.read()
                if not ret and self.loop_file:
                    try:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    except Exception:
                        pass
                    ret, frame = self.cap.read()
                if not ret:
                    if Config.DEBUG:
                        print("[YoloService] Video stream ended or frame read failed")
                    break

                frame_count += 1
                frame = self._resize_if_needed(frame)
                row = self._clone_frame(frame)
                with self.frame_lock:
                    self._last_row = self._clone_frame(row)

                should_infer = (
                    frame_count == 1
                    or frame_count % n == 0
                    or self._last_processed_is_none()
                )
                if should_infer:
                    self._enqueue_infer(frame)

                if self._file_frame_period > 0:
                    elapsed = time.perf_counter() - t0
                    wait = self._file_frame_period - elapsed
                    if wait > 0:
                        time.sleep(wait)
        finally:
            self.running = False
            self._signal_infer_shutdown()

    def _inference_loop(self) -> None:
        while True:
            try:
                item = self.infer_queue.get(timeout=0.5)
            except queue.Empty:
                if not self.running:
                    break
                continue
            if item is None:
                break
            try:
                processed, row_out, bird_view = self.model.track(item)
                with self.frame_lock:
                    self._last_processed = self._clone_frame(processed)
                    self._last_row = self._clone_frame(row_out)
                    self._last_bird = self._clone_frame(bird_view)
            except Exception as e:
                print(f"[YoloService] Inference error: {e}")

    def start(self) -> None:
        self.running = True
        try:
            if Config.DEBUG:
                print(f"[YoloService] Starting video processing with model: {self.model}")
            self._capture_thread = Thread(target=self._capture_loop, daemon=True)
            self._infer_thread = Thread(target=self._inference_loop, daemon=True)
            self._capture_thread.start()
            self._infer_thread.start()
            self._capture_thread.join()
            self._infer_thread.join()
        except Exception as e:
            print(f"[YoloService] Error during processing: {e}")
        finally:
            if Config.DEBUG:
                print("[YoloService] Releasing resources")
            self.release()

    def get_statistics(self):
        return self.model.get_statistics()

    def _snapshot(self, attr):
        with self.frame_lock:
            f = getattr(self, attr)
            return f.copy() if isinstance(f, np.ndarray) else None

    def get_row_frame(self):
        frame = self._snapshot("_last_row")
        if frame is not None:
            return frame
        return None

    def get_processed_frame(self):
        frame = self._snapshot("_last_processed")
        if frame is not None:
            return frame
        return self._snapshot("_last_row")

    def get_birdView_frame(self):
        return self._snapshot("_last_bird")

    def release(self) -> None:
        self.running = False
        self._signal_infer_shutdown()
        try:
            self.cap.release()
        except Exception:
            pass
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=4)
        if self._infer_thread and self._infer_thread.is_alive():
            self._infer_thread.join(timeout=30)
        self.model.reset_statistics()
