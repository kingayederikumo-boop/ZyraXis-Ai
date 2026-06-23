import json
from app.core.queue import Queue
from app.core.logger import get_logger

logger = get_logger(__name__)

DLQ_CHANNEL = "zyraxis_dlq"

queue = Queue()


def push_dlq(job: dict, error: str):
    payload = {
        "job": job,
        "error": error,
    }

    success = queue.push(DLQ_CHANNEL, payload)

    if success:
        logger.warning(f"Job moved to DLQ: {payload}")
    else:
        logger.error("Failed to push job to DLQ")


def get_dlq_job():
    return queue.pop(DLQ_CHANNEL)
