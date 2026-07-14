import os
import asyncio

from app.workers.telegram_consumer_v2 import run as run_v2


def main():
    mode = os.getenv("WORKER_MODE", "v2")

    if mode != "v2":
        raise RuntimeError("Only v2 worker is supported. Set WORKER_MODE=v2")

    # FIX: run_v2 (telegram_consumer_v2.run) is async now - calling it as a
    # plain function would just create a coroutine object and return
    # immediately without ever executing its body. Process would have
    # printed the startup line then exited clean with zero work done and
    # zero error - a silent failure, worse than a crash.
    asyncio.run(run_v2())


if __name__ == "__main__":
    main()