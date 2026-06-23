from typing import Dict, Any, Optional


class BillingService:
    """
    Lightweight billing enforcement layer.
    Acts as gatekeeper before worker execution.
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

    def __init__(self, usage_store: Optional[Dict[str, Any]] = None):
        # placeholder for Redis/Supabase usage tracking
        self.usage_store = usage_store or {}

    def can_execute(self, user_id: str, action_type: str, tier: str = "free") -> bool:
        """
        Returns whether user is allowed to execute action.
        """

        limits = self.TIERS.get(tier, self.TIERS["free"])

        key = f"{user_id}:{action_type}"
        used = self.usage_store.get(key, 0)

        allowed = limits.get(f"{action_type}_per_day")
        if allowed is None:
            return False

        return used < allowed

    def record_usage(self, user_id: str, action_type: str):
        key = f"{user_id}:{action_type}"
        self.usage_store[key] = self.usage_store.get(key, 0) + 1

    def reset_usage(self, user_id: str):
        for k in list(self.usage_store.keys()):
            if k.startswith(f"{user_id}:"):
                self.usage_store[k] = 0
