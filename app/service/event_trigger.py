# -*- coding: utf-8 -*-
"""
事件触发器
用于控制结构化状态何时进入大模型推理，避免逐帧调用。
"""
from typing import Dict, Tuple

from app.config.config import Config


class EventTrigger:
    def __init__(
        self,
        fixed_interval_seconds: float = 2.0,
        min_alert_count: int = 1,
        scene_change_threshold: int = 1,
        enable_fixed_interval: bool = True,
        force_risk_levels=None,
    ):
        self.fixed_interval_seconds = fixed_interval_seconds
        self.min_alert_count = min_alert_count
        self.scene_change_threshold = scene_change_threshold
        self.enable_fixed_interval = enable_fixed_interval
        self.force_risk_levels = set(force_risk_levels or {"high", "critical"})
        self.last_trigger_timestamp = 0.0
        self.last_signature = None

    def should_trigger(self, scene_data: Dict, rules_result: Dict) -> Tuple[bool, str]:
        timestamp = float(scene_data.get("timestamp", 0.0))
        alert_count = int(rules_result.get("alert_count", 0))
        risk_level = rules_result.get("risk_level", "low")
        signature = self._build_signature(scene_data, rules_result)

        if risk_level in self.force_risk_levels:
            self._mark_trigger(timestamp, signature)
            return True, f"risk_level:{risk_level}"

        if alert_count >= self.min_alert_count and self._scene_changed(signature):
            self._mark_trigger(timestamp, signature)
            return True, "scene_changed"

        if self.enable_fixed_interval and (timestamp - self.last_trigger_timestamp) >= self.fixed_interval_seconds:
            self._mark_trigger(timestamp, signature)
            return True, "fixed_interval"

        return False, "suppressed"

    def _scene_changed(self, signature: Tuple) -> bool:
        if self.last_signature is None:
            return True
        changed_items = sum(
            1 for current, previous in zip(signature, self.last_signature) if current != previous
        )
        return changed_items >= self.scene_change_threshold

    def _mark_trigger(self, timestamp: float, signature: Tuple):
        self.last_trigger_timestamp = timestamp
        self.last_signature = signature

    def _build_signature(self, scene_data: Dict, rules_result: Dict) -> Tuple:
        use_track = getattr(Config, "ENABLE_TRACKING", False)

        def _coarse_key(obj):
            pos = obj.get("image_position") or [0, 0]
            return (
                obj.get("class_name"),
                round(float(pos[0]) / 80.0),
                round(float(pos[1]) / 80.0),
            )

        if use_track:
            worker_ids = tuple(sorted(w.get("track_id") for w in scene_data.get("workers", [])))
            vehicle_ids = tuple(sorted(v.get("track_id") for v in scene_data.get("vehicles", [])))
        else:
            worker_ids = tuple(sorted(_coarse_key(w) for w in scene_data.get("workers", [])))
            vehicle_ids = tuple(sorted(_coarse_key(v) for v in scene_data.get("vehicles", [])))
        abnormal_stays = tuple(sorted(scene_data.get("abnormal_stays", [])))
        alert_types = tuple(sorted(alert.get("type") for alert in rules_result.get("alerts", [])))
        return (
            scene_data.get("worker_count", 0),
            scene_data.get("vehicle_count", 0),
            worker_ids,
            vehicle_ids,
            abnormal_stays,
            rules_result.get("risk_level", "low"),
            alert_types,
        )
