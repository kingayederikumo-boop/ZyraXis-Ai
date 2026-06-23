import json
import time
from typing import Dict, Any

from app.queue.producer import QueueProducer
from app.core.job_schema import JobValidator
from app.core.logger import get_logger

logger = get_logger("telegram_webhook")


class TelegramWebhook:
    def __init__(self, redis_url: str):
        self.producer = QueueProducer(redis_url)
        self.validator = JobValidator()

    def handle_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Entry point for Telegram webhook payloads.
        Converts Telegram update -> internal job schema -> queue.
        """

        try:
            job = self._convert_to_job(update)

            if not self.validator.validate(job):
                logger.warning("invalid_update", update=update)
                return {"status": "rejected"}

            job = self.validator.normalize(job).__dict__

            self.producer.push(job)

            logger.info("job_enqueued", job_id=job.get("job_id"))

            return {"status": "accepted", "job_id": job.get("job_id")}

        except Exception as e:
            logger.error("webhook_error", error=str(e))
            return {"status": "error"}

    def _convert_to_job(self, update: Dict[str, Any]) -> Dict[str, Any]:
        message = update.get("message", {})
        text = message.get("text", "")
        user_id = message.get("from", {}).get("id")

        return {
            "job_id": f"tg_{user_id}_{int(time.time()*1000)}",
            "type": "chat",
            "payload": {
                "text": text,
                "user_id": user_id,
                "raw": update
            },
            "retries": 0
        }
