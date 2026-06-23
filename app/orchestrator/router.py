from app.providers.openrouter_client import OpenRouterClient
from app.gateway.guard import Gatekeeper
from app.gateway.auth import AuthService
from app.database.session import SessionLocal
from app.ops.logger import OpsLogger

client = OpenRouterClient()
gate = Gatekeeper()
auth = AuthService()
logger = OpsLogger()

class Orchestrator:
    """V1.3 ops-integrated execution core."""

    def handle_message(self, telegram_id: str, text: str):
        db = SessionLocal()

        logger.event("request_received", telegram_id, {"text_length": len(text)})

        try:
            user = auth.get_or_create_user(telegram_id)
            is_premium = bool(user.is_premium)

            usage_row = db.execute(
                "SELECT ai_requests FROM usage WHERE telegram_id = :tid",
                {"tid": telegram_id}
            ).fetchone()

            usage_count = usage_row[0] if usage_row else 0

            if not gate.can_use_ai(usage_count, is_premium=is_premium):
                logger.event("quota_denied", telegram_id, {"usage": usage_count, "premium": is_premium})
                return "Daily limit reached. Upgrade to premium."

            try:
                response = client.chat(text)
            except Exception as e:
                logger.error("ai_error", telegram_id, str(e))
                return "AI service temporarily unavailable. Try again later."

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

            logger.event("ai_success", telegram_id, {"usage_after": usage_count + 1})

            return response

        finally:
            db.close()