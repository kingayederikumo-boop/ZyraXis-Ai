import json
import redis
from app.config import Config
from app.core.logger import get_logger

logger = get_logger(__name__)


class Queue:
    def __init__(self):
        self.redis = None
        if hasattr(Config, "REDIS_URL") and Config.REDIS_URL:
            self.redis = redis.from_url(Config.REDIS_URL, decode_responses=True)

    def enabled(self) -> bool:
        return self.redis is not None

    def push(self, channel: str, payload: dict):
        if not self.enabled():
            logger.warning("Queue disabled - running in sync mode")
            return False

        self.redis.lpush(channel, json.dumps(payload))
        return True

    def pop(self, channel: str):
        if not self.enabled():
            return None

        data = self.redis.rpop(channel)
        if data:
            return json.loads(data)
        return None
