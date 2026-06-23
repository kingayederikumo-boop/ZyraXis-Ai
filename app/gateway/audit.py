from datetime import datetime

class AuditLogger:
    def log_event(self, event_type: str, user_id: str, data: dict | None = None):
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "data": data or {}
        }
        print(payload)

    def log_block(self, user_id: str, reason: str):
        self.log_event("BLOCK", user_id, {"reason": reason})

    def log_usage(self, user_id: str, feature: str):
        self.log_event("USAGE", user_id, {"feature": feature})
