from fastapi import FastAPI, Request
import os
import json
import time
import redis
from app.config import Config
from app.database.session import init_db
from app.bot.telegram_client import answer_pre_checkout_query_async
from app.bot.payments import parse_invoice_payload

app = FastAPI()

_redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
QUEUE_NAME = "telegram_updates"

@app.on_event("startup")
async def startup():
    Config.validate()
    init_db()

@app.get("/health")
async def health():
    return {"status": "ok"}

# ... (rest of main.py from attachment)