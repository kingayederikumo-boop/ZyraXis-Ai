"""V1.1 subscription tiers and media quota matrix.

Revision ID: 0003
Revises: 0002

Adds the Plus tier, adds image_generation as a separately metered feature,
and replaces the old 3-tier quota matrix with the frozen V1.1 matrix.

Quota semantics:
- daily_limit >= 0: hard daily quota
- daily_limit = -1: unlimited for normal users, with application-level
  fair-use/abuse protection where applicable

Expert roleplay is intentionally unlimited. Expert chat uses a high internal
ceiling (100/day) so the backend remains protected while the UI presents it
as high daily usage/fair use.
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

QUOTAS = {
    "free": {"chat": 10, "roleplay": 3, "uploads": 2, "image_generation": 2, "image_edit": 1, "video": 0},
    "pro": {"chat": 25, "roleplay": 10, "uploads": 5, "image_generation": 5, "image_edit": 3, "video": 2},
    "plus": {"chat": 40, "roleplay": 30, "uploads": 10, "image_generation": 12, "image_edit": 8, "video": 6},
    "expert": {"chat": 100, "roleplay": -1, "uploads": 25, "image_generation": 30, "image_edit": 20, "video": 20},
}


def _drop_constraints():
    # DROP ... IF EXISTS avoids aborting the PostgreSQL transaction if a
    # hardened production database has already removed one of these names.
    for table, name in (
        ("users", "users_tier_check"),
        ("subscriptions", "subscriptions_tier_check"),
        ("payment_events", "payment_events_tier_check"),
        ("feature_limits", "feature_limits_tier_check"),
        ("usage_events", "usage_events_feature_check"),
        ("feature_limits", "feature_limits_feature_check"),
        ("feature_limits", "feature_limits_daily_limit_check"),
    ):
        op.execute(sa.text(f'ALTER TABLE "{table}" DROP CONSTRAINT IF EXISTS "{name}"'))


def upgrade():
    _drop_constraints()

    op.create_check_constraint("users_tier_check", "users", "tier IN ('free', 'pro', 'plus', 'expert')")
    op.create_check_constraint("subscriptions_tier_check", "subscriptions", "tier IN ('free', 'pro', 'plus', 'expert')")
    op.create_check_constraint("payment_events_tier_check", "payment_events", "tier IN ('pro', 'plus', 'expert')")
    op.create_check_constraint(
        "usage_events_feature_check", "usage_events",
        "feature IN ('chat', 'roleplay', 'uploads', 'image_generation', 'image_edit', 'video')",
    )
    op.create_check_constraint("feature_limits_tier_check", "feature_limits", "tier IN ('free', 'pro', 'plus', 'expert')")
    op.create_check_constraint(
        "feature_limits_feature_check", "feature_limits",
        "feature IN ('chat', 'roleplay', 'uploads', 'image_generation', 'image_edit', 'video')",
    )
    op.create_check_constraint("feature_limits_daily_limit_check", "feature_limits", "daily_limit >= -1")

    # feature_limits is configuration, not historical usage. Rebuild the
    # matrix deterministically so every tier has every metered capability.
    op.execute(sa.text("DELETE FROM feature_limits"))
    rows = [
        {"tier": tier, "feature": feature, "daily_limit": daily_limit}
        for tier, features in QUOTAS.items()
        for feature, daily_limit in features.items()
    ]
    op.bulk_insert(
        sa.table(
            "feature_limits",
            sa.column("tier", sa.Text),
            sa.column("feature", sa.Text),
            sa.column("daily_limit", sa.Integer),
        ),
        rows,
    )


def downgrade():
    _drop_constraints()

    op.create_check_constraint("users_tier_check", "users", "tier IN ('free', 'pro', 'expert')")
    op.create_check_constraint("subscriptions_tier_check", "subscriptions", "tier IN ('free', 'pro', 'expert')")
    op.create_check_constraint("payment_events_tier_check", "payment_events", "tier IN ('pro', 'expert')")
    op.create_check_constraint(
        "usage_events_feature_check", "usage_events",
        "feature IN ('chat', 'roleplay', 'uploads', 'image_edit', 'video')",
    )
    op.create_check_constraint("feature_limits_tier_check", "feature_limits", "tier IN ('free', 'pro', 'expert')")
    op.create_check_constraint(
        "feature_limits_feature_check", "feature_limits",
        "feature IN ('chat', 'roleplay', 'uploads', 'image_edit', 'video')",
    )
    op.create_check_constraint("feature_limits_daily_limit_check", "feature_limits", "daily_limit >= 0")

    op.execute(sa.text("DELETE FROM feature_limits"))
    old_quotas = {
        "free": {"chat": 10, "roleplay": 3, "uploads": 2, "image_edit": 1, "video": 0},
        "pro": {"chat": 25, "roleplay": 10, "uploads": 5, "image_edit": 3, "video": 2},
        "expert": {"chat": 100, "roleplay": 60, "uploads": 25, "image_edit": 20, "video": 20},
    }
    rows = [
        {"tier": tier, "feature": feature, "daily_limit": limit}
        for tier, features in old_quotas.items()
        for feature, limit in features.items()
    ]
    op.bulk_insert(
        sa.table(
            "feature_limits",
            sa.column("tier", sa.Text),
            sa.column("feature", sa.Text),
            sa.column("daily_limit", sa.Integer),
        ),
        rows,
    )
