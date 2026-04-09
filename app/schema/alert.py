from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AlertEvent:
    timestamp: float
    risk_level: str
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    decision: Optional[Dict[str, Any]] = None
