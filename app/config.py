import os

class Config:
    """Core configuration with strict env validation."""

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    OPENROUTER_API_KEY_CHAT = os.getenv("OPENROUTER_API_KEY_CHAT") or OPENROUTER_API_KEY
    OPENROUTER_API_KEY_ROLEPLAY = os.getenv("OPENROUTER_API_KEY_ROLEPLAY") or OPENROUTER_API_KEY
    OPENROUTER_API_KEY_CODE = os.getenv("OPENROUTER_API_KEY_CODE") or OPENROUTER_API_KEY
    OPENROUTER_API_KEY_SEARCH = os.getenv("OPENROUTER_API_KEY_SEARCH") or OPENROUTER_API_KEY
    OPENROUTER_API_KEY_IMAGE = os.getenv("OPENROUTER_API_KEY_IMAGE") or OPENROUTER_API_KEY
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENROUTER_API_KEY_FILE = os.getenv("OPENROUTER_API_KEY_FILE") or OPENROUTER_API_KEY
    OPENROUTER_API_KEY_VIDEO = os.getenv("OPENROUTER_API_KEY_VIDEO") or OPENROUTER_API_KEY

    OPENROUTER_MODEL_CHAIN = os.getenv(
        "OPENROUTER_MODEL_CHAIN",
        "anthropic/claude-sonnet-4.6,openai/gpt-5.4,google/gemini-3.1-pro-preview",
    ).split(",")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///zyraxis.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    ENV = os.getenv("ENV", "development")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # Quotas are intentionally NOT hardcoded here. Production quota truth
    # lives in the feature_limits table and is read by Gatekeeper.
    # Expert roleplay uses -1 in feature_limits to represent unlimited,
    # subject to backend fair-use safeguards.

    TIER_PRICE_STARS = {
        "pro": 200,
        "plus": 500,
        "expert": 1100,
    }

    VALID_TIERS = ("free", "pro", "plus", "expert")

    @classmethod
    def validate(cls):
        required = ["OPENROUTER_API_KEY"]
        missing = []

        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")

        for key in required:
            if not getattr(cls, key, None):
                missing.append(key)

        if missing:
            raise RuntimeError(f"Missing required config: {', '.join(missing)}")

        return True
