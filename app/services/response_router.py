from typing import Dict, Any, Optional


class ResponseRouter:
    """
    Translates internal execution results into user-facing responses.
    Used to close feedback loop for billing, errors, and success states.
    """

    def build_success(self, job: Dict[str, Any], result: Any) -> Dict[str, Any]:
        return {
            "status": "success",
            "job_id": job.get("job_id"),
            "correlation_id": job.get("correlation_id"),
            "data": result,
        }

    def build_error(
        self,
        job: Dict[str, Any],
        error: str
    ) -> Dict[str, Any]:
        return {
            "status": "error",
            "job_id": job.get("job_id"),
            "correlation_id": job.get("correlation_id"),
            "error": error,
        }

    def build_billing_block(
        self,
        job: Dict[str, Any],
        action_type: str,
        tier: str
    ) -> Dict[str, Any]:
        return {
            "status": "blocked",
            "reason": "billing_limit_reached",
            "action_type": action_type,
            "tier": tier,
            "job_id": job.get("job_id"),
            "correlation_id": job.get("correlation_id"),
        }
