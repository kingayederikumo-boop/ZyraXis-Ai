"""
Worker liveness signal. Rewritten fresh for this clean rebuild - a Redis
key with a short TTL that the worker refreshes periodically. Lets you
answer "is the worker actually alive right now" with one Redis GET,
without needing to check a hosting platform's dashboard.
"""

import os
import time
import threading
import redis
import datetime

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
_redis = redis.from_url(REDIS_URL, decode_responses=True)

HEARTBEAT_KEY = "zyraxis:worker:heartbeat"
HEARTBEAT_TTL_SECONDS = 90
HEARTBEAT_INTERVAL_SECONDS = 30


def _beat_loop():
    while True:
        try:
            _redis.set(HEARTBEAT_KEY, datetime.datetime.utcnow().isoformat(), ex=HEARTBEAT_TTL_SECONDS)
        except Exception as e:
            print(f"Heartbeat write failed: {e}")
        time.sleep(HEARTBEAT_INTERVAL_SECONDS)


def start_heartbeat():
    """Runs in a background thread so it never blocks the main consumer
    loop. Check liveness with: redis-cli GET zyraxis:worker:heartbeat"""
    thread = threading.Thread(target=_beat_loop, daemon=True)
    thread.start()
