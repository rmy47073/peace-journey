# -*- coding: utf-8 -*-
"""
推理决策引擎
结合规则引擎和大模型进行智能决策
"""
from typing import Dict, List, Optional
from app.ai.deepseek_client import DeepSeekClient


class ReasoningEngine:
    """智能推理决策引擎"""

    def __init__(self, deepseek_client: Optional[DeepSeekClient] = None):
        """
        初始化推理引擎

        Args:
            deepseek_client: DeepSeek客户端实例（可选）
        """
        self.deepseek_client = deepseek_client
        self.decision_history = []

    def make_decision(self, scene_data: Dict, rules_result: Dict) -> Dict:
        """
        综合规则引擎和AI推理做出决策

        Args:
            scene_data: 场景数据
            rules_result: 规则引擎检测结果

        Returns:
            决策结果
        """
        decision = {
            "timestamp": scene_data.get("timestamp"),
            "rule_based_alerts": rules_result.get("alerts", []),
            "ai_analysis": None,
            "final_decision": {},
            "confidence": 0.0
        }

        # 基于规则的初步决策
        rule_risk_level = self._assess_rule_risk(rules_result)
        decision["rule_risk_level"] = rule_risk_level

        # 如果配置了DeepSeek，使用AI增强决策
        if self.deepseek_client and self._should_use_ai(rules_result):
            ai_result = self.deepseek_client.analyze_scene(scene_data)
            if ai_result:
                decision["ai_analysis"] = ai_result
                decision["final_decision"] = self._merge_decisions(
                    rules_result, ai_result
                )
                decision["confidence"] = 0.9
            else:
                # AI调用失败，仅使用规则
                decision["final_decision"] = self._rule_only_decision(rules_result)
                decision["confidence"] = 0.7
        else:
            # 仅使用规则引擎
            decision["final_decision"] = self._rule_only_decision(rules_result)
            decision["confidence"] = 0.8

        self.decision_history.append(decision)
        return decision

    def _assess_rule_risk(self, rules_result: Dict) -> str:
        """评估规则检测的风险等级"""
        alerts = rules_result.get("alerts", [])
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

    def _should_use_ai(self, rules_result: Dict) -> bool:
        """判断是否需要使用AI增强决策"""
        # 复杂场景或高风险情况使用AI
        alerts = rules_result.get("alerts", [])
        return len(alerts) >= 2 or any(
            a.get("level") in ["critical", "high"] for a in alerts
        )

    def _merge_decisions(self, rules_result: Dict, ai_result: Dict) -> Dict:
        """合并规则和AI的决策结果"""
        return {
            "risk_level": self._merge_risk_levels(
                rules_result.get("risk_level", "low"),
                ai_result.get("risk_level", "low")
            ),
            "alerts": rules_result.get("alerts", []),
            "ai_risks": ai_result.get("risks", []),
            "suggestions": ai_result.get("suggestions", []),
            "immediate_actions": ai_result.get("immediate_actions", []),
            "reasoning": ai_result.get("reasoning", "")
        }

    def _rule_only_decision(self, rules_result: Dict) -> Dict:
        """仅基于规则的决策"""
        return {
            "risk_level": rules_result.get("risk_level", "low"),
            "alerts": rules_result.get("alerts", []),
            "suggestions": self._generate_rule_suggestions(rules_result)
        }

    def _merge_risk_levels(self, rule_level: str, ai_level: str) -> str:
        """合并风险等级，取较高者"""
        levels = ["low", "medium", "high", "critical"]
        rule_idx = levels.index(rule_level) if rule_level in levels else 0
        ai_idx = levels.index(ai_level) if ai_level in levels else 0
        return levels[max(rule_idx, ai_idx)]

    def _generate_rule_suggestions(self, rules_result: Dict) -> List[str]:
        """基于规则生成建议"""
        suggestions = []
        for alert in rules_result.get("alerts", []):
            alert_type = alert.get("type")
            if alert_type == "worker_in_danger_zone":
                suggestions.append("立即疏散危险区域内的工人")
            elif alert_type == "vehicle_speeding":
                suggestions.append("提醒车辆减速，加强交通管制")
            elif alert_type == "no_safety_equipment":
                suggestions.append("要求工人佩戴安全装备")
        return suggestions
