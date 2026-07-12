"""
AuthService - matches the real schema: users.telegram_id IS the primary
key (bigint), there's no separate autoincrement id. Tier changes write to
subscriptions (history) as well as updating users.tier - previously this
only ever touched a single boolean/column and never recorded history that
the rest of the schema (subscriptions table) was clearly designed to hold.
"""

from app.database.session import SessionLocal
from app.database.models import User, Subscription
from app.config import Config


class AuthService:
    def get_or_create_user(self, telegram_id, username: str = None):
        tid = int(telegram_id)
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == tid).first()

            if not user:
                user = User(telegram_id=tid, username=username, tier="free")
                db.add(user)
                db.commit()
                db.refresh(user)

            return user
        finally:
            db.close()

    def get_tier(self, telegram_id) -> str:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == int(telegram_id)).first()
            return user.tier if user else "free"
        finally:
            db.close()

    def get_mode(self, telegram_id) -> str:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == int(telegram_id)).first()
            return user.current_mode if user else "chat"
        finally:
            db.close()

    def set_mode(self, telegram_id, mode: str):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == int(telegram_id)).first()
            if user:
                user.current_mode = mode
                db.commit()
        finally:
            db.close()

    def is_admin(self, telegram_id) -> bool:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == int(telegram_id)).first()
            return bool(user.is_admin) if user else False
        finally:
            db.close()

    def set_tier(self, telegram_id, tier: str, stars_paid: int = 0):
        """Called after Stars payment success or /premiumadd. Updates the
        fast-lookup users.tier AND writes a subscriptions history row -
        the schema clearly intends subscriptions to hold this, and nothing
        wrote to it before this pass."""
        if tier not in Config.VALID_TIERS:
            raise ValueError(f"Invalid tier: {tier}")

        tid = int(telegram_id)
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == tid).first()
            if not user:
                return

            user.tier = tier
            db.add(Subscription(
                telegram_id=tid, tier=tier, status="active", stars_paid=stars_paid,
            ))
            db.commit()
        finally:
            db.close()
