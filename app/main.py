from fastapi import FastAPI, Request
from telegram import Update

from app.config import Config
from app.bot.telegram_bot import build_app
from app.bot.webhook_setup import register_webhook

app = FastAPI()
telegram_app = build_app()

# Optional webhook registration (safe for serverless cold starts)
try:
    register_webhook()
except Exception:
    pass


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(req: Request):
    """
    Telegram webhook entrypoint
    """
    data = await req.json()

    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)

    return {"ok": True}


def bootstrap():
    # Fail-fast validation of environment before any service starts
    Config.validate()


if __name__ == "__main__":
    bootstrap()
    print("ZyraXis bootstrap validation passed.")