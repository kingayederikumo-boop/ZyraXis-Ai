from app.providers.openrouter_client import OpenRouterClient
from app.gateway.guard import Gatekeeper
from app.gateway.auth import AuthService
from app.database.session import SessionLocal

client = OpenRouterClient()
gate = Gatekeeper()
auth = AuthService()

class Orchestrator:
    """V1.2 hardened execution core (single source of truth)."""

    def handle_message(self, telegram_id: str, text: str):
        db = SessionLocal()

        try:
            # Resolve user (DB is single source of truth)
            user = auth.get_or_create_user(telegram_id)

            # Enforce premium state from DB only
            is_premium = bool(user.is_premium)

            # Gate enforcement (AI usage only)
            if not gate.can_use_ai(user_usage := 0, is_premium=is_premium):
                return "Daily limit reached. Upgrade to premium."

            # Execute AI call with safety wrapper
            try:
                response = client.chat(text)
            except Exception:
                return "AI service temporarily unavailable. Try again later."

            # Atomic usage update (DB truth)
            usage = db.execute(
                "SELECT ai_requests FROM usage WHERE telegram_id = :tid",
                {"tid": telegram_id}
            ).fetchone()

            if usage:
                db.execute(
                    "UPDATE usage SET ai_requests = ai_requests + 1 WHERE telegram_id = :tid",
                    {"tid": telegram_id}
                )
            else:
                db.execute(
                    "INSERT INTO usage (telegram_id, date, ai_requests) VALUES (:tid, date('now'), 1)",
                    {"tid": telegram_id}
                )

            db.commit()

            return response

        finally:
            db.close()