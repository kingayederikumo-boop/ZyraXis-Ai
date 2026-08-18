"""SQLAlchemy models matching the production schema.

The production database is the source of truth. Do not use
Base.metadata.create_all() as a substitute for the Alembic/Supabase schema.
"""

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, BigInteger, Integer, Text, Boolean, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(BigInteger, primary_key=True)
    username = Column(Text, nullable=True)
    first_seen = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    last_seen = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    # DB constraint: free | pro | plus | expert
    tier = Column(Text, default="free", nullable=False)
    status = Column(Text, default="active", nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    current_mode = Column(Text, default="chat", nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    @property
    def is_premium(self) -> bool:
        return self.tier != "free"


class UsageEvent(Base):
    """One row per use.

    DB feature values: chat, roleplay, uploads, image_generation,
    image_edit, video.
    """

    __tablename__ = "usage_events"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    feature = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class PaymentEvent(Base):
    """Immutable Telegram Stars payment ledger.

    telegram_payment_id is unique and is the idempotency key. Paid tiers:
    pro, plus, expert.
    """

    __tablename__ = "payment_events"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    telegram_payment_id = Column(Text, unique=True, nullable=False)
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    tier = Column(Text, nullable=False)
    stars = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class Subscription(Base):
    """Subscription history. Tier changes update users.tier and append here."""

    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    tier = Column(Text, nullable=False)
    status = Column(Text, default="active")
    stars_paid = Column(Integer, default=0)
    activated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class FeatureLimit(Base):
    """Tier x feature quota matrix.

    daily_limit >= 0 is a daily quota. daily_limit == -1 is an unlimited
    entitlement, currently used for Expert roleplay with fair-use safeguards.
    """

    __tablename__ = "feature_limits"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tier = Column(Text, nullable=False)
    feature = Column(Text, nullable=False)
    daily_limit = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    chat_id = Column(Text, nullable=False)
    job_id = Column(Text, unique=True, nullable=False)
    polling_url = Column(Text, nullable=False)
    status = Column(Text, default="pending")
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    feature = Column(Text, nullable=False)
    role = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
