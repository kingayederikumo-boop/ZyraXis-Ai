from app.database.session import SessionLocal
from app.database.models import User

class AuthService:
    """Handles user resolution and premium state for monetization layer."""

    def get_or_create_user(self, telegram_id: str):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()

            if not user:
                user = User(telegram_id=telegram_id, is_premium=False)
                db.add(user)
                db.commit()
                db.refresh(user)

            return user
        finally:
            db.close()

    def is_premium(self, telegram_id: str) -> bool:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            return bool(user and user.is_premium)
        finally:
            db.close()

    def upgrade_to_premium(self, telegram_id: str):
        """Called after Telegram Stars payment success."""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.is_premium = True
                db.commit()
        finally:
            db.close()
