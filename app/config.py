import os

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///zyraxis.db")

    FREE_DAILY_LIMIT = 10
    ROLEPLAY_LIMIT = 5
    IMAGE_LIMIT = 3
