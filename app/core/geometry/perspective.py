import cv2
import numpy as np


def transform_point(matrix: np.ndarray, x: float, y: float):
    src_point = np.array([[[x, y]]], dtype=np.float32)
    dst_point = cv2.perspectiveTransform(src_point, matrix)
    return dst_point[0][0]
