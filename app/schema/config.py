from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class VideoSourceConfig:
    cap_type: str
    cap_path: str
    src_points: List[dict]
    danger_zones: List[list] = field(default_factory=list)
    enable_ai: bool = False
    service_name: Optional[str] = None
