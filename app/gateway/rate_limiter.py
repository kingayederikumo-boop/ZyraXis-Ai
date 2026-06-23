from datetime import datetime
from app.gateway.redis_client import redis_client

class RateLimiter:
    """Redis-backed atomic rate limiter for ZyraXis gateway."""

    def _key(self, user_id: str, feature: str) -> str:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return f"usage:{user_id}:{feature}:{today}"

    def get_usage(self, user_id: str, feature: str) -> int:
        try:
            value = redis_client.get(self._key(user_id, feature))
            return int(value) if value else 0
        except Exception:
            # Fail-open: assume no usage tracking available
            return 0

    def increment(self, user_id: str, feature: str) -> int:
        try:
            return redis_client.incr(self._key(user_id, feature))
        except Exception:
            # Fail-open: allow usage but do not track
            return 0

    def can_use(self, user_id: str, feature: str, limit: int) -> bool:
        try:
            return self.get_usage(user_id, feature) < limit
        except Exception:
            # Fail-open: allow request if Redis is down
            return True
