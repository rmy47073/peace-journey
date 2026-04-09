import cv2


def point_in_polygon(zone, point) -> bool:
    return cv2.pointPolygonTest(zone, point, False) >= 0
