"""Gatekeeper - reads real quotas from feature_limits and real usage from
usage_events. Quotas are database truth, not hardcoded application values.

Quota semantics:
- daily_limit >= 0: normal daily quota
- daily_limit == -1: unlimited entitlement
"""

import datetime

from sqlalchemy import func
from app.database.session import SessionLocal
from app.database.models import FeatureLimit, UsageEvent

FEATURE_TO_DB_EVENT = {
    "chat": "chat",
    "roleplay": "roleplay",
    "image": "image_generation",
    "image_generation": "image_generation",
    "image_edit": "image_edit",
    "file": "uploads",
    "uploads": "uploads",
    "video": "video",
    # Search and code do not have independent usage buckets yet. Their
    # capability access is still tier-gated by the orchestrator; until their
    # own quota buckets exist, usage is charged to the chat bucket.
    "search": "chat",
    "code": "chat",
}


class Gatekeeper:
    def _limit(self, tier: str, db_feature: str) -> int:
        db = SessionLocal()
        try:
            row = db.query(FeatureLimit).filter(
                FeatureLimit.tier == tier,
                FeatureLimit.feature == db_feature,
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

        # -1 is the explicit unlimited entitlement used by Expert roleplay.
        if limit == -1:
            return True

        return self._usage_today(telegram_id, db_feature) < limit

    def remaining(self, telegram_id: int, tier: str, feature: str) -> int:
        db_feature = FEATURE_TO_DB_EVENT.get(feature, "chat")
        limit = self._limit(tier, db_feature)

        if limit == -1:
            return -1

        used = self._usage_today(telegram_id, db_feature)
        return max(0, limit - used)

    def usage_percent(self, telegram_id: int, tier: str, feature: str) -> int | None:
        """Return percentage used for UI. None represents unlimited."""
        db_feature = FEATURE_TO_DB_EVENT.get(feature, "chat")
        limit = self._limit(tier, db_feature)
        if limit == -1:
            return None
        if limit <= 0:
            return 100
        used = self._usage_today(telegram_id, db_feature)
        return min(100, int((used / limit) * 100))
