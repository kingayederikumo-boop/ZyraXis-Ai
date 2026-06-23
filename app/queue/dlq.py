import os
import json
import time
import redis

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")

client = redis.from_url(REDIS_URL, decode_responses=True)

DLQ_KEY = "telegram_dlq"
RETRY_KEY = "telegram_retry"


def push_dlq(event: dict, error: str):
    payload = {
        "event": event,
        "error": error,
        "timestamp": time.time(),
        "retry_count": event.get("retry_count", 0),
    }

    client.lpush(DLQ_KEY, json.dumps(payload))


def push_retry(event: dict):
    event["retry_count"] = event.get("retry_count", 0) + 1

    client.lpush(RETRY_KEY, json.dumps(event))


def pop_retry():
    item = client.brpop(RETRY_KEY, timeout=5)

    if not item:
        return None

    _, raw = item
    return json.loads(raw)
