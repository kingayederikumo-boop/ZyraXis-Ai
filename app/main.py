from fastapi import FastAPI, Request
import os
import json
import time

import redis

from app.config import Config

app = FastAPI()

# Redis queue setup (ingestion layer)
_redis = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
QUEUE_NAME = "telegram_updates"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(req: Request):
    """
    Ingestion-only webhook.
    Pushes Telegram updates into Redis queue.
    """
    data = await req.json()

    event = {
        "id": data.get("update_id") or str(time.time()),
        "timestamp": time.time(),
        "payload": data,
    }

    _redis.lpush(QUEUE_NAME, json.dumps(event))

    return {"ok": True}


def bootstrap():
    Config.validate()


if __name__ == "__main__":
    bootstrap()
    print("ZyraXis bootstrap validation passed.")