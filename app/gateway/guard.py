"""
Gatekeeper - reads real quotas from feature_limits (already populated in
production with 15 rows) and counts real usage from usage_events (one row
per use, not a counter column). Previously this read hardcoded placeholder
numbers from Config.LIMITS, which never matched the real database at all.
"""

import datetime

from sqlalchemy import func
from app.database.session import SessionLocal
from app.database.models import FeatureLimit, UsageEvent

# The app's internal feature names don't map 1:1 onto the DB's
# usage_events/feature_limits enum (chat, roleplay, uploads, image_edit,
# video). search and code have no dedicated quota in the schema - the spec
# never defined one either - so both share the chat bucket.
FEATURE_TO_DB_EVENT = {
    "chat": "chat",
    "roleplay": "roleplay",
    "image": "image_edit",
    "file": "uploads",
    "video": "video",
    "search": "chat",
    "code": "chat",
}


class Gatekeeper:
    def _limit(self, tier: str, db_feature: str) -> int:
        db = SessionLocal()
        try:
            row = db.query(FeatureLimit).filter(
                FeatureLimit.tier == tier, FeatureLimit.feature == db_feature
            ).first()
            return row.daily_limit if row else 0
        finally:
            db.close()

    def _usage_today(self, telegram_id: int, db_feature: str) -> int:
        today_start = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        db = SessionLocal()
        try:
            return db.query(func.count(UsageEvent.id)).filter(
                UsageEvent.telegram_id == telegram_id,
                UsageEvent.feature == db_feature,
                UsageEvent.created_at >= today_start,
            ).scalar() or 0
        finally:
            db.close()

    def can_use(self, telegram_id: int, tier: str, feature: str) -> bool:
        db_feature = FEATURE_TO_DB_EVENT.get(feature, "chat")
        limit = self._limit(tier, db_feature)
        return self._usage_today(telegram_id, db_feature) < limit

    def remaining(self, telegram_id: int, tier: str, feature: str) -> int:
        db_feature = FEATURE_TO_DB_EVENT.get(feature, "chat")
        limit = self._limit(tier, db_feature)
        used = self._usage_today(telegram_id, db_feature)
        return max(0, limit - used)
