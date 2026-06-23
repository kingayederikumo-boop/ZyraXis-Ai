from typing import Dict, Any

from app.workers.base_worker import BaseWorker
from app.core.idempotency import IdempotencyStore
from app.services.billing import BillingService
from app.services.response_router import ResponseRouter


class ChatWorker(BaseWorker):
    def __init__(self, redis_url: str):
        super().__init__(name="chat_worker")
        self.idempotency = IdempotencyStore(redis_url)
        self.billing = BillingService(usage_store={})
        self.router = ResponseRouter()

    def run_job(self, job: Dict[str, Any], handler):
        job_id = job.get("job_id")
        cid = job.get("correlation_id")

        user_id = job.get("payload", {}).get("user_id")
        action_type = "ai"
        tier = job.get("payload", {}).get("tier", "free")

        if user_id and not self.billing.can_execute(user_id, action_type, tier):
            self.logger.warning(
                "billing_blocked",
                job_id=job_id,
                correlation_id=cid,
                user_id=user_id
            )
            return self.router.build_billing_block(job, action_type, tier)

        if job_id and not self.idempotency.ensure_once(f"chat:{job_id}"):
            return None

        self.logger.info("chat_job_start", job_id=job_id, correlation_id=cid)

        try:
            result = handler(job)

            if user_id:
                self.billing.record_usage(user_id, action_type)

            self.logger.info("chat_job_success", job_id=job_id, correlation_id=cid)
            return self.router.build_success(job, result)

        except Exception as e:
            self.logger.error("chat_job_failed", job_id=job_id, error=str(e), correlation_id=cid)
            return self.router.build_error(job, str(e))
