import os
from typing import Dict, Any, Optional

from app.repositories.usage import UsageRepository
from app.repositories.subscriptions import SubscriptionRepository


class BillingService:
    """
    Lightweight billing enforcement layer.
    Now upgraded with Redis-backed persistence + Supabase tier resolution.
    """

    TIERS = {
        "free": {
            "ai_per_day": 10,
            "roleplay_per_day": 3,
            "uploads_per_day": 2,
            "image_edits_per_day": 1,
        },
        "pro": {
            "ai_per_day": 60,
            "roleplay_per_day": 20,
            "uploads_per_day": 10,
            "image_edits_per_day": 7,
        },
        "expert": {
            "ai_per_day": 180,
            "roleplay_per_day": 80,
            "uploads_per_day": 50,
            "image_edits_per_day": 30,
        },
    }

    def __init__(
        self,
        usage_store: Optional[Dict[str, Any]] = None,
        redis_url: Optional[str] = None,
    ):
        self.usage_store = usage_store if usage_store is not None else None

        self.repo = None
        self.subscription_repo = None

        redis_url = redis_url or os.getenv("REDIS_URL")

        # usage repository (Redis)
        if redis_url:
            try:
                self.repo = UsageRepository(redis_url)
            except Exception:
                self.repo = None

        # subscription repository (Supabase)
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if supabase_url and supabase_key:
            try:
                self.subscription_repo = SubscriptionRepository(
                    supabase_url, supabase_key
                )
            except Exception:
                self.subscription_repo = None

        if self.usage_store is None and self.repo is None:
            self.usage_store = {}

    def can_execute(
        self,
        user_id: str,
        action_type: str,
        tier: str = "free",
    ) -> bool:
        # resolve tier from Supabase if available
        resolved_tier = tier

        if self.subscription_repo and user_id:
            try:
                resolved_tier = self.subscription_repo.get_tier(user_id)
            except Exception:
                resolved_tier = tier

        limits = self.TIERS.get(resolved_tier, self.TIERS["free"])
        allowed = limits.get(f"{action_type}_per_day")

        if allowed is None:
            return False

        if self.repo:
            used = self.repo.get(user_id, action_type)
        else:
            key = f"{user_id}:{action_type}"
            used = self.usage_store.get(key, 0)

        return used < allowed

    def record_usage(self, user_id: str, action_type: str):
        if self.repo:
            self.repo.incr(user_id, action_type)
            return

        key = f"{user_id}:{action_type}"
        self.usage_store[key] = self.usage_store.get(key, 0) + 1

    def reset_usage(self, user_id: str):
        if self.repo:
            self.repo.reset_user(user_id)
            return

        for k in list(self.usage_store.keys()):
            if k.startswith(f"{user_id}:"):
                self.usage_store[k] = 0
