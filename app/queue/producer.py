import json
from typing import Any, Dict

try:
    import redis
except ImportError:
    redis = None


class QueueProducer:
    def __init__(self, redis_url: str, channel: str = "zyraxis_queue"):
        if redis is None:
            raise RuntimeError("redis-py is required")

        self.client = redis.from_url(redis_url, decode_responses=True)
        self.channel = channel

    def push(self, job: Dict[str, Any]) -> bool:
        try:
            payload = json.dumps(job)
            self.client.lpush(self.channel, payload)
            return True
        except Exception:
            return False

    def push_priority(self, job: Dict[str, Any]) -> bool:
        try:
            payload = json.dumps(job)
            self.client.rpush(self.channel, payload)
            return True
        except Exception:
            return False
