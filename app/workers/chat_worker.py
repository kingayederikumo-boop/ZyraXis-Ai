from typing import Dict, Any

from app.workers.base_worker import BaseWorker
from app.core.idempotency import IdempotencyStore


class ChatWorker(BaseWorker):
    def __init__(self, redis_url: str):
        super().__init__(name="chat_worker")
        self.idempotency = IdempotencyStore(redis_url)

    def run_job(self, job: Dict[str, Any], handler):
        job_id = job.get("job_id")
        if job_id and not self.idempotency.ensure_once(f"chat:{job_id}"):
            return

        return handler(job)
