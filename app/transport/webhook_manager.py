import requests
from app.config import Config


def set_webhook():
    """Registers webhook URL with Telegram API."""
    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/setWebhook"

    payload = {"url": Config.WEBHOOK_URL}
    response = requests.post(url, json=payload, timeout=10)

    return response.json()


def delete_webhook():
    """Removes webhook from Telegram API."""
    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/deleteWebhook"

    response = requests.post(url, timeout=10)
    return response.json()
