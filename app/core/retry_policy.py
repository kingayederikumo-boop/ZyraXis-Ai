from dataclasses import dataclass
from enum import Enum
import time
import random


class FailureType(str, Enum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    TIMEOUT = "timeout"


@dataclass
class RetryConfig:
    max_retries: int = 5
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0
    backoff_multiplier: float = 2.0
    jitter: bool = True


class RetryPolicy:
    def __init__(self, config: RetryConfig = RetryConfig()):
        self.config = config

    def classify_error(self, error: Exception) -> FailureType:
        msg = str(error).lower()

        if "timeout" in msg:
            return FailureType.TIMEOUT
        if "validation" in msg or "invalid" in msg:
            return FailureType.PERMANENT
        return FailureType.TRANSIENT

    def should_retry(self, attempt: int, failure_type: FailureType) -> bool:
        if failure_type == FailureType.PERMANENT:
            return False
        return attempt < self.config.max_retries

    def get_delay(self, attempt: int) -> float:
        delay = min(
            self.config.base_delay * (self.config.backoff_multiplier ** attempt),
            self.config.max_delay,
        )

        if self.config.jitter:
            delay *= random.uniform(0.8, 1.2)

        return delay

    def sleep_backoff(self, attempt: int):
        time.sleep(self.get_delay(attempt))
