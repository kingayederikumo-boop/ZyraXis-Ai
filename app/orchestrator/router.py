from app.providers.openrouter_client import OpenRouterClient
from app.gateway.guard import Gatekeeper
from app.gateway.auth import AuthService
from app.database.session import SessionLocal

client = OpenRouterClient()
gate = Gatekeeper()
auth = AuthService()

class Orchestrator:
    """V1.2 hardened execution core (atomic enforcement fix)."""

    def handle_message(self, telegram_id: str, text: str):
        db = SessionLocal()

        try:
            # Resolve user (DB is single source of truth)
            user = auth.get_or_create_user(telegram_id)

            # Enforce premium state strictly from DB
            is_premium = bool(user.is_premium)

            # Fetch real usage from DB (NO SPOOF)
            usage_row = db.execute(
                "SELECT ai_requests FROM usage WHERE telegram_id = :tid",
                {"tid": telegram_id}
            ).fetchone()

            usage_count = usage_row[0] if usage_row else 0

            # Gate enforcement (correct usage-based limit)
            if not gate.can_use_ai(usage_count, is_premium=is_premium):
                return "Daily limit reached. Upgrade to premium."

            # Execute AI call with safety wrapper
            try:
                response = client.chat(text)
            except Exception:
                return "AI service temporarily unavailable. Try again later."

            # Atomic usage update (DB truth)
            if usage_row:
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