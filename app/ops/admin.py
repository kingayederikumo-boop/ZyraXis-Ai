from app.database.session import SessionLocal
from app.database.models import User

class OpsAdmin:
    """Minimal admin controls for ZyraXis ops layer."""

    def set_premium(self, telegram_id: str, value: bool):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.is_premium = value
                db.commit()
        finally:
            db.close()

    def get_user(self, telegram_id: str):
        db = SessionLocal()
        try:
            return db.query(User).filter(User.telegram_id == telegram_id).first()
        finally:
            db.close()