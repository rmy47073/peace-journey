class EventService:
    def merge_alert_payload(self, rules_result, decision):
        return {
            "risk_level": rules_result.get("risk_level", "low"),
            "alerts": rules_result.get("alerts", []),
            "decision": decision,
        }
