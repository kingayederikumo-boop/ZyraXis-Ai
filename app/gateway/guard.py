"""Gatekeeper - reads real quotas from feature_limits and real usage from
usage_events. Quotas are database truth, not hardcoded application values.

Quota semantics (confirmed live against the actual database, not assumed):
- daily_limit >= 0: normal daily quota, checked as usage_today < daily_limit
- There is no -1/"unlimited" sentinel in production. Expert's fair-use
  chat/roleplay limits are a large finite number (1000/day) in
  feature_limits directly - inventing a special -1 meaning here would
  contradict what's actually in the database.
"""

import datetime

from sqlalchemy import func
from app.database.session import SessionLocal
from app.database.models import FeatureLimit, UsageEvent

# FIX: usage_events.feature has a real CHECK constraint in production:
# ANY(['chat', 'roleplay', 'uploads', 'image_edit', 'video']). This dict
# previously mapped "image" -> "image_generation", a value that doesn't
# exist in that constraint - every successful /image call was failing at
# the very last step (saving the usage event) with a DB constraint
# violation. Image generation and image editing intentionally share one
# bucket (image_edit) - confirmed decision, not an oversight.
FEATURE_TO_DB_EVENT = {
    "chat": "chat",
    "roleplay": "roleplay",
    "image": "image_edit",
    "file": "uploads",
    "video": "video",
    # Search and code have no independent usage bucket in the schema -
    # charged to chat until/unless a dedicated bucket is added.
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
        return self._usage_today(telegram_id, db_feature) < limit

    def remaining(self, telegram_id: int, tier: str, feature: str) -> int:
        db_feature = FEATURE_TO_DB_EVENT.get(feature, "chat")
        limit = self._limit(tier, db_feature)
        used = self._usage_today(telegram_id, db_feature)
        return max(0, limit - used)

    def usage_percent(self, telegram_id: int, tier: str, feature: str) -> int:
        """Percentage used today, for UI display."""
        db_feature = FEATURE_TO_DB_EVENT.get(feature, "chat")
        limit = self._limit(tier, db_feature)
        if limit <= 0:
            return 100
        used = self._usage_today(telegram_id, db_feature)
        return min(100, int((used / limit) * 100))
