import os

class Config:
    """Core configuration with strict env validation."""

    def _require(self, key: str, default: str | None = None):
        value = os.getenv(key, default)
        if value is None or value == "":
            raise RuntimeError(f"Missing required environment variable: {key}")
        return value

    # Core services
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    # Storage
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///zyraxis.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Runtime safety flags
    ENV = os.getenv("ENV", "development")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # Hard limits (free tier baseline)
    FREE_AI_LIMIT = 20
    FREE_ROLEPLAY_LIMIT = 5
    FREE_IMAGE_LIMIT = 3
    FREE_FILE_LIMIT = 5

    # Premium tier baseline
    PREMIUM_AI_LIMIT = 30
    PREMIUM_ROLEPLAY_LIMIT = 15
    PREMIUM_IMAGE_LIMIT = 5
    PREMIUM_FILE_LIMIT = 10

    @classmethod
    def validate(cls):
        """Validate critical runtime configuration."""
        required = ["TELEGRAM_BOT_TOKEN", "OPENROUTER_API_KEY"]
        missing = []

        for key in required:
            if not getattr(cls, key, None):
                missing.append(key)

        if missing:
            raise RuntimeError(f"Missing required config: {', '.join(missing)}")

        return True
