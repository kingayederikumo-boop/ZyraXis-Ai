from fastapi import FastAPI, Request
import os
import json
import time
import redis
from app.config import Config
from app.database.session import init_db
from app.bot.telegram_client import answer_pre_checkout_query_async, get_bot
from app.bot.payments import parse_invoice_payload

app = FastAPI()

_redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
QUEUE_NAME = "telegram_updates"


@app.on_event("startup")
async def startup():
    Config.validate()
    init_db()

    # Registers the webhook with Telegram automatically on every boot -
    # replaces the manual `curl .../setWebhook?url=...` step, which was
    # easy to forget after a redeploy and fails silently (bot just goes
    # quiet, no error anywhere obvious) if skipped. Deliberately not
    # required in Config.validate() - unset means "skip," so local/dev
    # runs without a public URL don't crash on boot.
    if Config.WEBHOOK_URL:
        await get_bot().set_webhook(url=Config.WEBHOOK_URL)


@app.get("/health")
async def health():
    return {"status": "ok"}


async def handle_pre_checkout(pcq: dict):
    """Telegram gives the bot exactly 10 seconds to answer a
    pre_checkout_query, or the payment fails on the user's end. This has to
    happen here, directly in the webhook, NOT via the Redis queue - an
    earlier version of this code queued it, which meant the answer's timing
    depended on queue depth (unbounded). This bypasses that entirely, per
    the architecture decision already locked (see memory).

    Deliberately no DB call here - parse_invoice_payload and the price
    check are pure functions, keeping this fast enough to always clear
    the 10s window regardless of DB load.
    """
    pcq_id = pcq.get("id")
    payload = pcq.get("invoice_payload", "")
    amount = pcq.get("total_amount")

    parsed = parse_invoice_payload(payload)

    ok = True
    error_message = None

    if not parsed:
        ok = False
        error_message = "Invalid order — please try again from /premium."
    else:
        _telegram_id, tier = parsed
        if amount != Config.TIER_PRICE_STARS.get(tier):
            ok = False
            error_message = "Price mismatch — please reopen /premium and try again."

    try:
        await answer_pre_checkout_query_async(pcq_id, ok=ok, error_message=error_message)
    except Exception as e:
        print(f"pre_checkout answer failed: {e}")


@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    # Time-critical: answered here, synchronously, never queued.
    if "pre_checkout_query" in data:
        await handle_pre_checkout(data["pre_checkout_query"])
        return {"ok": True}

    # Everything else (messages, callback_queries, successful_payment
    # messages) isn't time-critical - goes through the normal queue.
    event = {
        "id": data.get("update_id") or str(time.time()),
        "timestamp": time.time(),
        "payload": data,
    }
    _redis.lpush(QUEUE_NAME, json.dumps(event))
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
