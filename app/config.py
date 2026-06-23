import os

class Config:
    """Core configuration with strict env validation."""

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_FATHER_TOKEN")
    OPENROUTER_API_TOKEN = os.getenv("OPENROUTER_API_TOKEN")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///zyraxis.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    ENV = os.getenv("ENV", "development")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    FREE_AI_LIMIT = 20
    FREE_ROLEPLAY_LIMIT = 5
    FREE_IMAGE_LIMIT = 3
    FREE_FILE_LIMIT = 5

    PREMIUM_AI_LIMIT = 30
    PREMIUM_ROLEPLAY_LIMIT = 15
    PREMIUM_IMAGE_LIMIT = 5
    PREMIUM_FILE_LIMIT = 10

    @classmethod
    def validate(cls):
        required = ["OPENROUTER_API_TOKEN"]
        missing = []

        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN or BOT_FATHER_TOKEN")

        for key in required:
            if not getattr(cls, key, None):
                missing.append(key)

        if missing:
            raise RuntimeError(f"Missing required config: {', '.join(missing)}")

        return True