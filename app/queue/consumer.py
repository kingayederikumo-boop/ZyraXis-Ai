import json
import time
from typing import Callable, Any, Dict

from app.core.retry_policy import RetryPolicy
from app.core.dlq import push_dlq

try:
    import redis
except ImportError:
    redis = None


class QueueConsumer:
    def __init__(self, redis_url: str, channel: str = "zyraxis_queue"):
        if redis is None:
            raise RuntimeError("redis-py is required")

        self.client = redis.from_url(redis_url, decode_responses=True)
        self.channel = channel
        self.retry_policy = RetryPolicy()

    def listen(self, handler: Callable[[Dict[str, Any]], None]):
        while True:
            try:
                _, data = self.client.brpop(self.channel, timeout=5)
                if not data:
                    continue

                job = json.loads(data)

                self._process(job, handler)

            except Exception as e:
                # global consumer failure
                time.sleep(1)

    def _process(self, job: Dict[str, Any], handler: Callable):
        retries = job.get("retries", 0)

        try:
            handler(job)

        except Exception as e:
            failure_type = self.retry_policy.classify_error(e)

            if self.retry_policy.should_retry(retries, failure_type):
                job["retries"] = retries + 1
                time.sleep(self.retry_policy.get_delay(retries))
                self.client.lpush(self.channel, json.dumps(job))
            else:
                push_dlq(job, str(e))
