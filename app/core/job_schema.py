from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class JobSchema:
    job_id: str
    type: str
    payload: Dict[str, Any]
    retries: int = 0
    max_retries: int = 5


class JobValidator:
    REQUIRED_FIELDS = ["job_id", "type", "payload"]

    def validate(self, job: Dict[str, Any]) -> bool:
        for field in self.REQUIRED_FIELDS:
            if field not in job:
                return False

        if not isinstance(job.get("payload"), dict):
            return False

        if job.get("retries", 0) < 0:
            return False

        return True

    def normalize(self, job: Dict[str, Any]) -> JobSchema:
        return JobSchema(
            job_id=job["job_id"],
            type=job["type"],
            payload=job["payload"],
            retries=job.get("retries", 0),
            max_retries=job.get("max_retries", 5),
        )
