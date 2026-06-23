import os

from app.workers.telegram_consumer_v2 import run as run_v2


def main():
    mode = os.getenv("WORKER_MODE", "v2")

    if mode != "v2":
        raise RuntimeError("Only v2 worker is supported in production. Set WORKER_MODE=v2")

    print("Starting ZyraXis Telegram Worker v2...")
    run_v2()


if __name__ == "__main__":
    main()
