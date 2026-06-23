import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zyraxis")

class OpsLogger:
    """Central event logger for ZyraXis ops layer."""

    def event(self, event_type: str, telegram_id: str, metadata: dict | None = None):
        payload = {
            "time": datetime.utcnow().isoformat(),
            "event": event_type,
            "user": telegram_id,
            "meta": metadata or {}
        }
        logger.info(payload)

    def error(self, event_type: str, telegram_id: str, error: str):
        logger.error({
            "time": datetime.utcnow().isoformat(),
            "event": event_type,
            "user": telegram_id,
            "error": error
        })