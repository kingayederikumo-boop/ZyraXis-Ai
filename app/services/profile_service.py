from app.database.session import SessionLocal
from app.database.models import User

class ProfileService:

    def get_profile(self, telegram_id: str):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return None

            return {
                "telegram_id": user.telegram_id,
                "is_premium": getattr(user, "is_premium", False),
                "created_at": str(user.created_at)
            }
        finally:
            db.close()
