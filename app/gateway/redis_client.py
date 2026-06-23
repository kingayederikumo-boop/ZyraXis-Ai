import redis
from app.config import Config

# Central Redis connection (singleton)
redis_client = redis.Redis.from_url(
    Config.REDIS_URL,
    decode_responses=True
)


def ping_redis() -> bool:
    """Validate Redis connectivity."""
    try:
        return redis_client.ping()
    except Exception:
        return False
