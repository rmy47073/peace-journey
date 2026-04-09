from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TrackObject:
    track_id: int
    class_name: str
    image_position: List[float]
    world_position: List[float]
    speed: float = 0.0
    in_hot_zone: bool = False
    bbox_xywh: List[float] = field(default_factory=list)
    bbox_xyxy: List[float] = field(default_factory=list)
    has_helmet: Optional[bool] = None


@dataclass
class SceneData:
    timestamp: float
    frame_count: int
    vehicle_count: int
    worker_count: int
    vehicles: List[dict] = field(default_factory=list)
    workers: List[dict] = field(default_factory=list)
    equipment: List[dict] = field(default_factory=list)
    objects: List[dict] = field(default_factory=list)
    danger_zone_objects: List[dict] = field(default_factory=list)
    fast_vehicles: List[dict] = field(default_factory=list)
    abnormal_stays: List[int] = field(default_factory=list)
