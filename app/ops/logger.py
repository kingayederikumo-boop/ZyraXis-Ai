"""
Structured event logging to the real event_logs table.

Rewritten fresh for this clean rebuild (the original version of this file
worked correctly and was never touched during the fix process - this
reimplementation preserves its call signature exactly:
logger.event(event_type, telegram_id, payload) / logger.error(event_type,
telegram_id, message) - but now targets the confirmed real schema
(event_logs: id, telegram_id, event_type, payload jsonb, created_at)
instead of assuming it.
"""

from app.database.session import SessionLocal
from app.database.models import Base
from sqlalchemy import Column, Text, BigInteger, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import datetime


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    telegram_id = Column(BigInteger, nullable=True)
    event_type = Column(Text, nullable=False)
    payload = Column(JSONB, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class OpsLogger:
    def event(self, event_type: str, telegram_id=None, payload: dict = None):
        db = SessionLocal()
        try:
            db.add(EventLog(
                telegram_id=int(telegram_id) if telegram_id else None,
                event_type=event_type,
                payload=payload or {},
            ))
            db.commit()
        except Exception as e:
            # Logging must never take down the request it's logging about.
            print(f"OpsLogger.event failed: {e}")
        finally:
            db.close()

    def error(self, event_type: str, telegram_id=None, message: str = ""):
        self.event(event_type, telegram_id, {"error": message})
