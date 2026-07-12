"""
SQLAlchemy models matching the REAL production schema in Supabase project
simbzoxqbuzvtgrvwmdj, built and hardened in earlier sessions (immutability
triggers, soft-delete, pg_cron jobs - none of that is re-declared here,
this just maps to what already exists).

IMPORTANT: this file previously declared a parallel, invented schema
(separate `usage`/`payments` tables, `users.id` autoincrement PK) that was
never checked against the real database. That version is gone. Everything
below matches actual production tables - do not run Base.metadata.create_all()
expecting to build users/usage_events/payment_events/subscriptions/
feature_limits from scratch; they already exist. create_all() only adds
video_jobs if it's ever missing (e.g. a fresh dev DB), and is a no-op
against tables that already exist by name.
"""

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, BigInteger, Integer, String, Text, Boolean, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(BigInteger, primary_key=True)
    username = Column(Text, nullable=True)
    first_seen = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    last_seen = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Check constraint (free|pro|expert) enforced at the DB level, not repeated here.
    tier = Column(Text, default="free", nullable=False)
    status = Column(Text, default="active", nullable=False)  # active|banned|suspended
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # non-NULL = soft-deleted

    # Added by this pass's migration - didn't exist before.
    current_mode = Column(Text, default="chat", nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    @property
    def is_premium(self) -> bool:
        return self.tier != "free"


class UsageEvent(Base):
    """One row PER USE, not a per-day counter column. Quota checks are
    COUNT(*) WHERE telegram_id=X AND feature=Y AND created_at >= today.
    feature is constrained at the DB level to: chat, roleplay, uploads,
    image_edit, video - NOT the app's internal feature names 1:1 (see
    FEATURE_TO_DB_EVENT mapping in app/gateway/guard.py)."""

    __tablename__ = "usage_events"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    feature = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class PaymentEvent(Base):
    """Immutable Stars payment ledger. telegram_payment_id uniquely
    constrained at the DB level - this IS the idempotency guard, not a
    separate payments table."""

    __tablename__ = "payment_events"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    telegram_payment_id = Column(Text, unique=True, nullable=False)
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    tier = Column(Text, nullable=False)  # constrained to pro|expert at the DB level
    stars = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class Subscription(Base):
    """History of subscription periods per user. A tier change should
    insert here as well as updating users.tier - this app previously only
    ever touched users.tier and never wrote subscription history."""

    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    tier = Column(Text, nullable=False)
    status = Column(Text, default="active")  # active|expired|cancelled|pending
    stars_paid = Column(Integer, default=0)
    activated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class FeatureLimit(Base):
    """Real tier x feature quota matrix, already populated with 15 rows in
    production. Gatekeeper reads FROM this table now - it does not use
    hardcoded Config.LIMITS anymore."""

    __tablename__ = "feature_limits"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tier = Column(Text, nullable=False)
    feature = Column(Text, nullable=False)
    daily_limit = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class VideoJob(Base):
    """New table (added this pass) - video generation is async (30s-minutes
    per OpenRouter), this tracks a submitted job across worker loop
    iterations until it completes."""

    __tablename__ = "video_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    chat_id = Column(Text, nullable=False)
    job_id = Column(Text, unique=True, nullable=False)
    polling_url = Column(Text, nullable=False)
    status = Column(Text, default="pending")  # pending|completed|failed|cancelled|expired
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
