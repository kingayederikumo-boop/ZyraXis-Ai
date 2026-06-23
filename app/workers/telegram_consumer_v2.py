import os
import json
import time
import requests
import redis

from app.orchestrator.router import Orchestrator
from app.queue.dlq import push_dlq, push_retry

QUEUE_NAME = "telegram_updates"

REDIS_URL = os.getenv("REDIS_URL")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)
orchestrator = Orchestrator()

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(chat_id: str, text: str):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=10,
        )
    except Exception as e:
        print(f"Telegram send failed: {e}")


def process_event(event: dict):
    try:
        payload = event.get("payload", {})

        message = payload.get("message", {})
        chat = message.get("chat", {})

        chat_id = str(chat.get("id"))
        text = message.get("text", "")
        user_id = str(message.get("from", {}).get("id", ""))

        if not chat_id or not text:
            return

        result = orchestrator.handle(user_id, text)

        if isinstance(result, dict):
            status = result.get("status")

            if status == "blocked":
                send_message(chat_id, "Limit reached. Upgrade required.")
                return

            if status == "error":
                send_message(chat_id, "System error occurred.")
                return

            if status == "success":
                send_message(chat_id, str(result.get("data")))
                return

        send_message(chat_id, str(result))

    except Exception as e:
        err = str(e)

        if "timeout" in err.lower() or "redis" in err.lower():
            push_retry(event)
        else:
            push_dlq(event, err)

        print(f"Processing failed: {e}")


def run():
    print("Telegram consumer v2 started...")

    while True:
        try:
            item = redis_client.brpop(QUEUE_NAME, timeout=5)

            if not item:
                continue

            _, raw = item
            event = json.loads(raw)

            process_event(event)

        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
