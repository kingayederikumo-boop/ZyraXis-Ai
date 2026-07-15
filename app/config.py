import os

class Config:
    """Core configuration with strict env validation."""

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    # Used at startup to auto-register the webhook with Telegram - see
    # app/main.py. Optional: if unset, startup just skips registration
    # (so local/dev runs without a public URL don't crash on boot).
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    # Optional per-feature keys, for spend-limit isolation on OpenRouter's
    # dashboard (image/video cost more per call than chat text - a separate
    # key with its own cap protects the main budget from one runaway
    # feature). Each falls back to OPENROUTER_API_KEY if unset - works out
    # of the box with just one key, upgrade to segmented keys anytime
    # without touching code.
    OPENROUTER_API_KEY_CHAT = os.getenv("OPENROUTER_API_KEY_CHAT") or OPENROUTER_API_KEY
    OPENROUTER_API_KEY_ROLEPLAY = os.getenv("OPENROUTER_API_KEY_ROLEPLAY") or OPENROUTER_API_KEY
    OPENROUTER_API_KEY_CODE = os.getenv("OPENROUTER_API_KEY_CODE") or OPENROUTER_API_KEY
    OPENROUTER_API_KEY_SEARCH = os.getenv("OPENROUTER_API_KEY_SEARCH") or OPENROUTER_API_KEY
    OPENROUTER_API_KEY_IMAGE = 
    # No longer used by the image feature specifically - OpenRouter's
    # Images API returned 402 Payment Required without a funded balance.
    # Image generation now uses Gemini's free tier instead (see below).
    # Left here in case OpenRouter image gen is revisited later.
    OPENROUTER_API_KEY_IMAGE = os.getenv("OPENROUTER_API_KEY_IMAGE") or OPENROUTER_API_KEY

    # Gemini API key for image generation (Nano Banana 2) - free tier,
    # 50 requests/day, no credit card required.
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENROUTER_API_KEY_FILE = os.getenv("OPENROUTER_API_KEY_FILE") or OPENROUTER_API_KEY
    OPENROUTER_API_KEY_VIDEO = os.getenv("OPENROUTER_API_KEY_VIDEO") or OPENROUTER_API_KEY

    # Fallback chain: OpenRouter tries these in order if one fails
    # (rate limit, 5xx, refusal, context-length error). Default list is
    # what you sent from OpenRouter's own example - override via env if
    # you want a different chain.
    OPENROUTER_MODEL_CHAIN = os.getenv(
        "OPENROUTER_MODEL_CHAIN",
        "anthropic/claude-sonnet-4.6,openai/gpt-5.4,google/gemini-3.1-pro-preview",
    ).split(",")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///zyraxis.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    ENV = os.getenv("ENV", "development")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # REMOVED: hardcoded LIMITS dict. Real per-tier, per-feature quotas
    # live in the `feature_limits` table in production (already populated
    # with 15 real rows) - Gatekeeper reads from there now, not from here.
    # This dict was placeholder guesses that never matched what was
    # actually in the database.

    # Telegram Stars pricing per spec
    TIER_PRICE_STARS = {
        "pro": 200,
        "expert": 1100,
    }

    VALID_TIERS = ("free", "pro", "expert")

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
