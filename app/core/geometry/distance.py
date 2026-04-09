import numpy as np


def euclidean_distance(point_a, point_b) -> float:
    return float(np.sqrt((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2))
