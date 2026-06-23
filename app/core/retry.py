import time
import random
from dataclasses import dataclass


@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 10.0
    backoff: float = 2.0
    jitter: float = 0.2


class RetryEngine:
    def __init__(self, policy: RetryPolicy = RetryPolicy()):
        self.policy = policy

    def execute(self, func, *args, **kwargs):
        last_error = None

        for attempt in range(self.policy.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e

                delay = min(
                    self.policy.base_delay * (self.policy.backoff ** attempt),
                    self.policy.max_delay,
                )

                jitter = random.uniform(0, self.policy.jitter)
                time.sleep(delay + jitter)

        raise last_error
