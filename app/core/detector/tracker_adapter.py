from typing import Dict


def normalize_track_object(track_object: Dict) -> Dict:
    return {
        "track_id": track_object.get("track_id"),
        "class_name": track_object.get("class_name"),
        "image_position": track_object.get("image_position", []),
        "world_position": track_object.get("world_position", []),
        "speed": track_object.get("speed", 0.0),
        "in_hot_zone": track_object.get("in_hot_zone", False),
        "bbox_xywh": track_object.get("bbox_xywh", []),
        "bbox_xyxy": track_object.get("bbox_xyxy", []),
    }
