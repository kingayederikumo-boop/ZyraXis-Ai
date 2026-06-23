from app.providers.openrouter import OpenRouterClient
from app.gateway.guard import Gatekeeper
from app.gateway.auth import AuthService
from app.database.session import SessionLocal
from app.ops.logger import OpsLogger
from app.core.engine import ExecutionEngine

auth = AuthService()
gate = Gatekeeper()
logger = OpsLogger()
engine = ExecutionEngine()

class Orchestrator:
    """V1.4 production orchestrator (ops-integrated, unified logging)."""

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
                logger.event("quota_denied", telegram_id, {"usage": usage_count})
                return "Daily limit reached. Upgrade required."

            try:
                response = engine.run("chat", text)
            except Exception as e:
                logger.error("ai_error", telegram_id, str(e))
                return "AI service temporarily unavailable."

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