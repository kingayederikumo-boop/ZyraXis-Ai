import time
from typing import Optional

try:
    import redis
except ImportError:
    redis = None


class UsageRepository:
    """
    Persistent usage tracking using Redis.
    Replaces in-memory billing counters.
    """

    def __init__(self, redis_url: str, namespace: str = "usage"):
        if redis is None:
            raise RuntimeError("redis-py is required")

        self.client = redis.from_url(redis_url, decode_responses=True)
        self.namespace = namespace

    def _key(self, user_id: str, action_type: str) -> str:
        return f"{self.namespace}:{user_id}:{action_type}:{self._day_key()}"

    def _day_key(self) -> str:
        return time.strftime("%Y-%m-%d")

    def incr(self, user_id: str, action_type: str, amount: int = 1) -> int:
        key = self._key(user_id, action_type)
        return self.client.incrby(key, amount)

    def get(self, user_id: str, action_type: str) -> int:
        key = self._key(user_id, action_type)
        value = self.client.get(key)
        return int(value) if value else 0

    def reset_user(self, user_id: str):
        pattern = f"{self.namespace}:{user_id}:*"
        for key in self.client.scan_iter(pattern):
            self.client.delete(key)
