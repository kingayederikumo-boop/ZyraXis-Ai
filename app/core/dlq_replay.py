import json
import time
from typing import Any, Dict

from app.core.job_schema import JobValidator
from app.core.idempotency import IdempotencyStore
from app.core.logger import get_logger

try:
    import redis
except ImportError:
    redis = None

logger = get_logger("dlq_replay")


class DLQReplay:
    def __init__(self, redis_url: str):
        if redis is None:
            raise RuntimeError("redis-py is required")

        self.client = redis.from_url(redis_url, decode_responses=True)
        self.dlq_channel = "zyraxis_dlq"
        self.queue_channel = "zyraxis_queue"

        self.validator = JobValidator()
        self.idempotency = IdempotencyStore(redis_url)

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

                logger.info("replay_attempt", job_id=job.get("job_id"))

                # validate before replay
                if not self.validator.validate(job):
                    logger.warning("replay_validation_failed", job_id=job.get("job_id"))
                    failed += 1
                    continue

                job = self.validator.normalize(job).__dict__

                # idempotency check
                key = f"replay:{job.get('job_id')}"
                if job.get("job_id") and not self.idempotency.ensure_once(key):
                    logger.warning("replay_duplicate_skipped", job_id=job.get("job_id"))
                    continue

                job["replayed_at"] = time.time()

                self.client.lpush(self.queue_channel, json.dumps(job))

                logger.info("replay_success", job_id=job.get("job_id"))
                success += 1

            except Exception as e:
                logger.error("replay_error", error=str(e))
                failed += 1

        return {
            "replayed": success,
            "failed": failed,
            "total": len(items)
        }
