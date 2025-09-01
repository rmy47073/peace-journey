import cv2
import numpy as np
from app.model.YoloModel import YoloModel

OUTPUT = True
SAVE = False
model_path = "D:\大创\yolo-track-master\models\yolov10n.pt"

if OUTPUT:
    cv2.namedWindow("birdView", cv2.WINDOW_NORMAL)
    cv2.namedWindow("row", cv2.WINDOW_NORMAL)
    cv2.namedWindow("processed", cv2.WINDOW_NORMAL)


yoloModel = YoloModel(model_path=model_path, traffic_flow=True,
                      src_points=np.array([[200, 500], [440, 500], [120, 850], [660, 850]], dtype=np.float32),
                      hot_zone=np.array([[200, 500], [440, 500], [120, 850], [660, 850]], dtype=np.float32),
                      stay_threshold=5,
                      num_lanes=4)  # 这里填写你的车道数

cap = cv2.VideoCapture("D:\大创\yolo-track-master\videos\test.mp4")
while True:
    ret, frame = cap.read()
    if not ret:
        break

    processed_frame, row_frame, birdView_frame = yoloModel.track(frame)
    if OUTPUT:
        cv2.imshow("processed", processed_frame)
        cv2.imshow("row", row_frame)
        cv2.imshow("birdView", birdView_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print(yoloModel.get_statistics())
        break

cv2.destroyAllWindows()




