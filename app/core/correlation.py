import uuid
from typing import Dict, Any, Optional


CORRELATION_KEY = "correlation_id"


def generate_id() -> str:
    return str(uuid.uuid4())


def extract_from_headers(headers: Optional[Dict[str, str]]) -> Optional[str]:
    if not headers:
        return None

    return (
        headers.get("X-Correlation-ID")
        or headers.get("x-correlation-id")
    )


def ensure(job: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Ensure job contains a correlation_id.
    Priority:
    1. existing job value
    2. headers
    3. generated
    """

    cid = job.get(CORRELATION_KEY)

    if not cid:
        cid = extract_from_headers(headers)

    if not cid:
        cid = generate_id()

    job[CORRELATION_KEY] = cid
    return job


def attach_log_context(data: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
    data[CORRELATION_KEY] = correlation_id
    return data
