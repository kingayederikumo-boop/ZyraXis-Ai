"""baseline - the real production schema (users, subscriptions,
usage_events, payment_events, event_logs, feature_limits, audit_logs)

Revision ID: 0001
Revises:
Create Date: 2026-07-09

This replaces an earlier 0001 that declared an entirely invented schema
(separate `usage`/`payments` tables, `users.id` autoincrement) which was
never checked against the actual database and doesn't match production
at all. This version reflects what's genuinely running in Supabase
project simbzoxqbuzvtgrvwmdj, built and hardened in earlier sessions.

Your production DB already has all of this - run 'alembic stamp head'
after this, NOT 'upgrade head'. This migration exists so a genuinely
fresh database (new dev environment, disaster recovery) can recreate
the real schema faithfully with 'alembic upgrade head'.

Note: this captures table/column/constraint structure only. Production
hardening details from earlier sessions (immutability triggers on
financial tables, pg_cron jobs for expiry/cleanup, BRIN indexes) are
infrastructure-level and intentionally not re-declared here - they're
DB-side objects this app's ORM layer doesn't need to know about to
function correctly.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("telegram_id", sa.BigInteger, primary_key=True),
        sa.Column("username", sa.Text, nullable=True),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("tier", sa.Text, nullable=False, server_default="free"),
        sa.Column("status", sa.Text, nullable=False, server_default="active"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "users_tier_check", "users", "tier IN ('free', 'pro', 'expert')"
    )
    op.create_check_constraint(
        "users_status_check", "users", "status IN ('active', 'banned', 'suspended')"
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("telegram_id", sa.BigInteger, sa.ForeignKey("users.telegram_id"), nullable=False),
        sa.Column("tier", sa.Text, nullable=False),
        sa.Column("status", sa.Text, server_default="active"),
        sa.Column("stars_paid", sa.Integer, server_default="0"),
        sa.Column("activated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_check_constraint(
        "subscriptions_tier_check", "subscriptions", "tier IN ('free', 'pro', 'expert')"
    )
    op.create_check_constraint(
        "subscriptions_status_check", "subscriptions",
        "status IN ('active', 'expired', 'cancelled', 'pending')"
    )

    op.create_table(
        "usage_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("telegram_id", sa.BigInteger, sa.ForeignKey("users.telegram_id"), nullable=False),
        sa.Column("feature", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_check_constraint(
        "usage_events_feature_check", "usage_events",
        "feature IN ('chat', 'roleplay', 'uploads', 'image_edit', 'video')"
    )

    op.create_table(
        "payment_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("telegram_payment_id", sa.Text, unique=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger, sa.ForeignKey("users.telegram_id"), nullable=False),
        sa.Column("tier", sa.Text, nullable=False),
        sa.Column("stars", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_check_constraint(
        "payment_events_tier_check", "payment_events", "tier IN ('pro', 'expert')"
    )
    op.create_check_constraint("payment_events_stars_check", "payment_events", "stars > 0")

    op.create_table(
        "event_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("telegram_id", sa.BigInteger, nullable=True),
        sa.Column("event_type", sa.Text, nullable=False),
        sa.Column("payload", sa.dialects.postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "feature_limits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tier", sa.Text, nullable=False),
        sa.Column("feature", sa.Text, nullable=False),
        sa.Column("daily_limit", sa.Integer, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_check_constraint(
        "feature_limits_tier_check", "feature_limits", "tier IN ('free', 'pro', 'expert')"
    )
    op.create_check_constraint(
        "feature_limits_feature_check", "feature_limits",
        "feature IN ('chat', 'roleplay', 'uploads', 'image_edit', 'video')"
    )
    op.create_check_constraint("feature_limits_daily_limit_check", "feature_limits", "daily_limit >= 0")

    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor", sa.Text, nullable=False),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("target_table", sa.Text, nullable=True),
        sa.Column("target_id", sa.Text, nullable=True),
        sa.Column("old_data", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("new_data", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("ip_address", sa.dialects.postgresql.INET, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # NOTE: seeding feature_limits' 15 real rows is deliberately NOT done
    # here - your production values are already there. A fresh dev DB
    # built from this migration will have an empty feature_limits table
    # and every quota check will deny everything (daily_limit defaults to
    # nothing) until you seed it - intentional, so dev doesn't silently
    # diverge from prod's real numbers by guessing at them again.


def downgrade():
    op.drop_table("audit_logs")
    op.drop_table("feature_limits")
    op.drop_table("event_logs")
    op.drop_table("payment_events")
    op.drop_table("usage_events")
    op.drop_table("subscriptions")
    op.drop_table("users")
