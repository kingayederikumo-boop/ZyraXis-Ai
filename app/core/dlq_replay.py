import json
import time
from typing import Any, Dict, Optional

try:
    import redis
except ImportError:
    redis = None


class DLQReplay:
    def __init__(self, redis_url: str):
        if redis is None:
            raise RuntimeError("redis-py is required")

        self.client = redis.from_url(redis_url, decode_responses=True)
        self.dlq_channel = "zyraxis_dlq"
        self.queue_channel = "zyraxis_queue"

    def fetch_batch(self, limit: int = 10):
        items = []

        for _ in range(limit):
            data = self.client.rpop(self.dlq_channel)
            if not data:
                break
            try:
                items.append(json.loads(data))
            except Exception:
                continue

        return items

    def replay(self, limit: int = 10) -> Dict[str, int]:
        items = self.fetch_batch(limit)

        success = 0
        failed = 0

        for item in items:
            try:
                job = item.get("job")

                if not job:
                    failed += 1
                    continue

                job["replayed_at"] = time.time()

                self.client.lpush(self.queue_channel, json.dumps(job))
                success += 1

            except Exception:
                failed += 1

        return {
            "replayed": success,
            "failed": failed,
            "total": len(items)
        }
