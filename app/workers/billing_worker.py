from typing import Dict, Any

from app.workers.base_worker import BaseWorker
from app.core.idempotency import IdempotencyStore
from app.services.billing import BillingService


class BillingWorker(BaseWorker):
    def __init__(self, redis_url: str):
        super().__init__(name="billing_worker")
        self.idempotency = IdempotencyStore(redis_url)
        self.billing = BillingService(redis_url=redis_url)

    def run_job(self, job: Dict[str, Any], handler):
        job_id = job.get("job_id")
        cid = job.get("correlation_id")

        user_id = job.get("payload", {}).get("user_id")
        action_type = job.get("payload", {}).get("action_type", "billing")
        tier = job.get("payload", {}).get("tier", "free")

        # billing gate (must pass before execution)
        if user_id and not self.billing.can_execute(user_id, action_type, tier):
            self.logger.warning(
                "billing_blocked",
                job_id=job_id,
                correlation_id=cid,
                user_id=user_id
            )
            return

        if job_id and not self.idempotency.ensure_once(f"billing:{job_id}"):
            return

        self.logger.info("billing_job_start", job_id=job_id, correlation_id=cid)

        try:
            result = handler(job)

            # record usage after successful execution
            if user_id:
                self.billing.record_usage(user_id, action_type)

            self.logger.info("billing_job_success", job_id=job_id, correlation_id=cid)
            return result

        except Exception as e:
            self.logger.error("billing_job_failed", job_id=job_id, error=str(e), correlation_id=cid)
            raise
