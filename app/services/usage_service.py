from datetime import datetime
from app.database.session import SessionLocal
from app.database.models import Usage

class UsageLookupService:

    def get_today(self, telegram_id: str):
        db = SessionLocal()
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")

            usage = (
                db.query(Usage)
                .filter(
                    Usage.telegram_id == telegram_id,
                    Usage.date == today
                )
                .first()
            )

            if not usage:
                return {
                    "ai_requests": 0,
                    "roleplay_requests": 0,
                    "image_requests": 0
                }

            return {
                "ai_requests": usage.ai_requests,
                "roleplay_requests": usage.roleplay_requests,
                "image_requests": usage.image_requests
            }
        finally:
            db.close()
