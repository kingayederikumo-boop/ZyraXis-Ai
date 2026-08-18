import os

class Config:
    """Compatibility configuration. Runtime imports app.config.Config."""

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///zyraxis.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    ENV = os.getenv("ENV", "development")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    TIER_PRICE_STARS = {
        "pro": 200,
        "plus": 500,
        "expert": 1100,
    }

    VALID_TIERS = ("free", "pro", "plus", "expert")
