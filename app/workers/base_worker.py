from typing import Callable, Any, Dict


class BaseWorker:
    def __init__(self, name: str):
        self.name = name

    def run_job(self, job: Dict[str, Any], handler: Callable):
        raise NotImplementedError

    def wrap_handler(self, handler: Callable):
        def wrapped(job: Dict[str, Any]):
            return self.run_job(job, handler)
        return wrapped
