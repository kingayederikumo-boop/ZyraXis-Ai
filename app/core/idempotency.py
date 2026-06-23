import time
from typing import Optional

try:
    import redis
except ImportError:
    redis = None


class IdempotencyStore:
    def __init__(self, redis_url: str, ttl: int = 3600):
        if redis is None:
            raise RuntimeError("redis-py is required")

        self.client = redis.from_url(redis_url, decode_responses=True)
        self.ttl = ttl

    def is_processed(self, key: str) -> bool:
        return self.client.exists(key) == 1

    def mark_processed(self, key: str) -> bool:
        try:
            # SETNX pattern
            result = self.client.set(key, "1", nx=True, ex=self.ttl)
            return bool(result)
        except Exception:
            return False

    def ensure_once(self, key: str) -> bool:
        """
        Returns True if allowed to proceed, False if duplicate.
        """
        return self.mark_processed(key)
