import os
import time
import threading
import redis

REDIS_URL = os.getenv("REDIS_URL")
WORKER_ID = os.getenv("WORKER_ID", "worker-v2")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

HEARTBEAT_KEY = "zyrax:worker:heartbeat"
INTERVAL = 10  # seconds


def _beat():
    while True:
        try:
            redis_client.hset(
                HEARTBEAT_KEY,
                WORKER_ID,
                str(int(time.time())),
            )
        except Exception as e:
            print(f"Heartbeat failed: {e}")

        time.sleep(INTERVAL)


def start_heartbeat():
    thread = threading.Thread(target=_beat, daemon=True)
    thread.start()
    return thread
