# -*- coding: utf-8 -*-
"""
规则引擎
定义和执行施工安全规则检测
"""
import cv2
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict


class SafetyRule:
    """安全规则基类"""

    def __init__(self, rule_id: str, name: str, level: str):
        self.rule_id = rule_id
        self.name = name
        self.level = level  # low, medium, high, critical

    def check(self, scene_data: Dict) -> List[Dict]:
        """检查规则，返回告警列表"""
        raise NotImplementedError


class WorkerInDangerZoneRule(SafetyRule):
    """工人进入危险区域规则"""

    def __init__(self, danger_zones: List[np.ndarray]):
        super().__init__("R001", "工人进入危险区域", "critical")
        self.danger_zones = danger_zones

    def check(self, scene_data: Dict) -> List[Dict]:
        alerts = []
        workers = scene_data.get("workers", [])

        for worker in workers:
            position = worker.get("image_position") or worker.get("position")
            if position and self._in_danger_zone(position):
                alerts.append({
                    "rule_id": self.rule_id,
                    "type": "worker_in_danger_zone",
                    "level": self.level,
                    "message": f"工人 ID:{worker.get('track_id')} 进入危险区域",
                    "object_id": worker.get("track_id"),
                    "position": position
                })

        return alerts

    def _in_danger_zone(self, position: Tuple[float, float]) -> bool:
        """检查位置是否在危险区域内"""
        for zone in self.danger_zones:
            if cv2.pointPolygonTest(zone, position, False) >= 0:
                return True
        return False


class VehicleSpeedingRule(SafetyRule):
    """车辆超速规则"""

    def __init__(self, speed_limit: float = 20.0):
        super().__init__("R002", "车辆超速", "high")
        self.speed_limit = speed_limit

    def check(self, scene_data: Dict) -> List[Dict]:
        alerts = []
        vehicles = scene_data.get("vehicles", [])

        for vehicle in vehicles:
            speed = vehicle.get("speed", 0)
            if speed > self.speed_limit:
                alerts.append({
                    "rule_id": self.rule_id,
                    "type": "vehicle_speeding",
                    "level": self.level,
                    "message": f"车辆 ID:{vehicle.get('track_id')} 超速 ({speed:.1f} km/h)",
                    "object_id": vehicle.get("track_id"),
                    "speed": speed
                })

        return alerts


class NoSafetyEquipmentRule(SafetyRule):
    """未佩戴安全装备规则"""

    def __init__(self):
        super().__init__("R003", "未佩戴安全装备", "high")

    def check(self, scene_data: Dict) -> List[Dict]:
        alerts = []
        workers = scene_data.get("workers", [])

        for worker in workers:
            if not worker.get("has_helmet", True):  # 假设有头盔检测
                alerts.append({
                    "rule_id": self.rule_id,
                    "type": "no_safety_equipment",
                    "level": self.level,
                    "message": f"工人 ID:{worker.get('track_id')} 未佩戴安全帽",
                    "object_id": worker.get("track_id")
                })

        return alerts


class VehicleWorkerProximityRule(SafetyRule):
    """车辆与工人距离过近规则"""

    def __init__(self, min_distance: float = 3.0):
        super().__init__("R004", "车辆与工人距离过近", "critical")
        self.min_distance = min_distance

    def check(self, scene_data: Dict) -> List[Dict]:
        alerts = []
        vehicles = scene_data.get("vehicles", [])
        workers = scene_data.get("workers", [])

        for vehicle in vehicles:
            v_pos = vehicle.get("world_position") or vehicle.get("position")
            if not v_pos:
                continue

            for worker in workers:
                w_pos = worker.get("world_position") or worker.get("position")
                if not w_pos:
                    continue

                distance = np.sqrt((v_pos[0] - w_pos[0])**2 + (v_pos[1] - w_pos[1])**2)

                if distance < self.min_distance:
                    alerts.append({
                        "rule_id": self.rule_id,
                        "type": "vehicle_worker_proximity",
                        "level": self.level,
                        "message": f"车辆 ID:{vehicle.get('track_id')} 与工人 ID:{worker.get('track_id')} 距离过近 ({distance:.1f}m)",
                        "vehicle_id": vehicle.get("track_id"),
                        "worker_id": worker.get("track_id"),
                        "distance": distance
                    })

        return alerts


class RuleEngine:
    """规则引擎主类"""

    def __init__(self):
        self.rules: List[SafetyRule] = []
        self.alert_history = defaultdict(list)

    def add_rule(self, rule: SafetyRule):
        """添加规则"""
        self.rules.append(rule)

    def remove_rule(self, rule_id: str):
        """移除规则"""
        self.rules = [r for r in self.rules if r.rule_id != rule_id]

    def evaluate(self, scene_data: Dict) -> Dict:
        """
        评估所有规则

        Args:
            scene_data: 场景数据

        Returns:
            评估结果，包含所有触发的告警
        """
        all_alerts = []

        for rule in self.rules:
            try:
                alerts = rule.check(scene_data)
                all_alerts.extend(alerts)
            except Exception as e:
                print(f"[RuleEngine] 规则 {rule.rule_id} 执行失败: {str(e)}")

        # 计算整体风险等级
        risk_level = self._calculate_risk_level(all_alerts)

        result = {
            "timestamp": scene_data.get("timestamp"),
            "alerts": all_alerts,
            "alert_count": len(all_alerts),
            "risk_level": risk_level
        }

        return result

    def _calculate_risk_level(self, alerts: List[Dict]) -> str:
        """根据告警计算整体风险等级"""
        if not alerts:
            return "low"

        critical_count = sum(1 for a in alerts if a.get("level") == "critical")
        high_count = sum(1 for a in alerts if a.get("level") == "high")

        if critical_count > 0:
            return "critical"
        elif high_count >= 2:
            return "high"
        elif high_count == 1:
            return "medium"
        else:
            return "low"

    def get_active_rules(self) -> List[Dict]:
        """获取所有活动规则"""
        return [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "level": rule.level
            }
            for rule in self.rules
        ]
