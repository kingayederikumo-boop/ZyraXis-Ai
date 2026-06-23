from app.providers.openrouter_client import OpenRouterClient
from app.gateway.guard import Gatekeeper
from app.gateway.rate_limiter import RateLimiter
from app.gateway.auth import AuthService
from app.gateway.usage import UsageService
from app.database.session import SessionLocal

client = OpenRouterClient()
gate = Gatekeeper()
limiter = RateLimiter()
auth = AuthService()
usage_service = UsageService()

class Orchestrator:
    """Core request pipeline with enforced gateway controls."""

    def handle_message(self, telegram_id: str, text: str, is_premium: bool = False):
        db = SessionLocal()

        try:
            # Resolve user
            user = auth.get_or_create_user(telegram_id)
            usage = usage_service.get_today_usage(db, telegram_id)

            # Enforce gate (AI usage only for now)
            if not gate.can_use_ai(telegram_id, is_premium):
                return "Daily limit reached. Upgrade to premium."

            # Double-check Redis layer (hard enforcement)
            if not limiter.can_use(telegram_id, "ai", 
                limit=1000000):  # gate already applied limits; this is safety layer
                return "Service temporarily unavailable due to usage limits."

            # Execute AI call
            response = client.chat(text)

            # Increment usage tracking
            usage_service.increment_ai(db, usage)
            limiter.increment(telegram_id, "ai")

            return response

        finally:
            db.close()
