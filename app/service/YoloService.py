import queue
from app.model.YoloModel import YoloModel
from threading import Lock
import cv2
import base64


class YoloService:
    """
    A service wrapper for the YoloModel, responsible for managing video capture,
    model inference, and returning various frame outputs to upstream consumers.
    """

    def __init__(self, model_path, src_points, cap, hot_zone=None, stay_threshold=5, traffic_flow=False, num_lanes=2):
        """
        Initialize the YoloService.

        Args:
            model_path (str): Path to the YOLO model file.
            src_points (np.array): Source points for perspective transform.
            cap (cv2.VideoCapture): OpenCV video capture object.
            hot_zone (ndarray, optional): Polygon coordinates for a special zone (e.g., no-parking zone).
            stay_threshold (int): Time (in seconds) after which a vehicle is considered as staying too long in hot zone.
            traffic_flow (bool): Whether to enable traffic flow counting (crossing middle line).
            num_lanes (int): Number of lanes to draw in the bird’s-eye view.
        """
        self.model = YoloModel(model_path, src_points, hot_zone, stay_threshold, traffic_flow, num_lanes)
        self.rowQueue = queue.Queue(maxsize=10)  # 从2增大到10
        self.processedQueue = queue.Queue(maxsize=10)
        self.birdViewQueue = queue.Queue(maxsize=10)
        self.cap = cap
        self.frame_lock = Lock()

    def try_put(self, q, item):
        try:
            q.put_nowait(item)
            print(f"[Debug] Put into {q.__class__.__name__}, size: {q.qsize()}")
        except queue.Full:
            # 只丢弃最旧帧如果队列已满
            if not q.empty():
                q.get_nowait()
                print(f"[Debug] Discarded oldest from {q.__class__.__name__}")
            q.put_nowait(item)

    def start(self):
        """
        Start reading frames from video stream and processing them with the model.
        """
        try:
            print(f"[YoloService] Starting video processing with model: {self.model}")
            frame_count = 0
            while True:
                ret, frame = self.cap.read()
                if ret:
                    frame_count += 1
                    print(f"[Debug] Processing frame {frame_count}")
                    processed, row, birdView = self.model.track(frame)
                    
                    # Debug print frame shapes
                    print(f"[Debug] Frame shapes - processed: {processed.shape if processed is not None else 'None'}, "
                          f"row: {row.shape if row is not None else 'None'}, "
                          f"birdView: {birdView.shape if birdView is not None else 'None'}")

                    # Queue the results
                    self.try_put(self.processedQueue, processed)
                    self.try_put(self.rowQueue, row)
                    self.try_put(self.birdViewQueue, birdView)
                else:
                    print("[YoloService] Video stream ended or frame read failed")
                    break
        except Exception as e:
            print(f"[YoloService] Error during processing: {e}")
        finally:
            print("[YoloService] Releasing resources")
            self.release()

    def get_statistics(self):
        """
        Retrieve the current vehicle tracking statistics.

        Returns:
            dict: Includes total count, category breakdown, long stays, and crossings.
        """
        return self.model.get_statistics()

    def get_row_frame(self):
        """
        Get the latest original (unprocessed) frame from the queue.

        Returns:
            np.ndarray or None: The raw frame if available, otherwise None.
        """
        if not self.rowQueue.empty():
            return self.rowQueue.get()
        return None

    def get_processed_frame(self):
        frame = self.processedQueue.get()
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')

    def get_birdView_frame(self):
        """
        Get the latest bird's-eye view frame showing vehicle trajectories.

        Returns:
            np.ndarray or None: The bird's-eye view frame if available, otherwise None.
        """
        if not self.birdViewQueue.empty():
            return self.birdViewQueue.get()
        return None

    def release(self):
        """
        Release resources including the video capture and reset tracking statistics.
        """
        self.cap.release()
        self.model.reset_statistics()
