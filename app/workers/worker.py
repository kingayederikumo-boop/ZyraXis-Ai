import time
import json

from app.core.queue import Queue
from app.core.runtime import handle_user
from app.core.logger import get_logger

logger = get_logger(__name__)

queue = Queue()

CHANNEL = "zyraxis_jobs"


def process_job(job: dict):
    try:
        user_id = job.get("user_id")
        text = job.get("text")

        if not user_id or not text:
            logger.warning(f"Invalid job payload: {job}")
            return

        result = handle_user(user_id, text)

        logger.info(json.dumps({
            "event": "job_processed",
            "user_id": user_id,
            "input": text,
            "output": result
        }))

    except Exception as e:
        logger.error(f"Worker error: {str(e)}")


def run_worker(poll_interval: float = 0.5):
    logger.info("Worker started")

    while True:
        job = queue.pop(CHANNEL)

        if job:
            process_job(job)
        else:
            time.sleep(poll_interval)
