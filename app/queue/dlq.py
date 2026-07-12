"""
Dead-letter and retry queue helpers, backed by the same Redis instance as
the main queue. Rewritten fresh for this clean rebuild - preserves the
call signature the worker already expects: push_dlq(event, error) /
push_retry(event).
"""

import os
import json
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
_redis = redis.from_url(REDIS_URL, decode_responses=True)

DLQ_NAME = "telegram_updates_dlq"
RETRY_NAME = "telegram_updates_retry"


def push_dlq(event: dict, error: str):
    """Unrecoverable failure - park it for manual inspection rather than
    losing it or retrying forever."""
    try:
        record = dict(event)
        record["_error"] = error
        _redis.lpush(DLQ_NAME, json.dumps(record))
    except Exception as e:
        print(f"push_dlq failed (event lost): {e}")


def push_retry(event: dict):
    """Transient failure (timeout, connection blip) - push to a separate
    retry list rather than straight back onto the main queue, so a
    poison-pill message can't infinite-loop the worker."""
    try:
        _redis.lpush(RETRY_NAME, json.dumps(event))
    except Exception as e:
        print(f"push_retry failed (event lost): {e}")
