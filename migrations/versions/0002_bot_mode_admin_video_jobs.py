"""add users.current_mode, users.is_admin, and video_jobs table

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-09

This is exactly what was already applied directly to production via
Supabase migration `add_bot_mode_admin_and_video_jobs` - this file exists
so Alembic's history matches reality for anyone rebuilding a fresh DB
later. Run 'alembic stamp head' on production (it's already there), only
use 'upgrade head' on a genuinely fresh database.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("current_mode", sa.Text, nullable=False, server_default="chat"))
    op.add_column("users", sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.false()))

    op.create_table(
        "video_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("telegram_id", sa.BigInteger, sa.ForeignKey("users.telegram_id"), nullable=False),
        sa.Column("chat_id", sa.Text, nullable=False),
        sa.Column("job_id", sa.Text, unique=True, nullable=False),
        sa.Column("polling_url", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_check_constraint(
        "video_jobs_status_check", "video_jobs",
        "status IN ('pending', 'completed', 'failed', 'cancelled', 'expired')"
    )
    # RLS: every other table in this schema has Row Level Security enabled;
    # video_jobs does not, by omission when it was first created. Not
    # auto-enabled here since a blind ALTER without matching policies can
    # silently block legitimate access - this is flagged to you separately,
    # not decided here.


def downgrade():
    op.drop_table("video_jobs")
    op.drop_column("users", "is_admin")
    op.drop_column("users", "current_mode")
