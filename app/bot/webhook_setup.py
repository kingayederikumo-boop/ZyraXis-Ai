import os
from telegram import Bot


def get_webhook_url() -> str:
    url = os.getenv("WEBHOOK_URL")
    if not url:
        raise RuntimeError("WEBHOOK_URL not set")
    return url


def get_bot() -> Bot:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    return Bot(token=token)


def register_webhook() -> dict:
    """
    Registers Telegram webhook for serverless deployment.
    Call once during deployment or cold start.
    """
    bot = get_bot()
    url = get_webhook_url()

    # Optional: drop pending updates for clean state
    result = bot.set_webhook(url=url, drop_pending_updates=True)

    return {
        "ok": result,
        "webhook_url": url,
    }
