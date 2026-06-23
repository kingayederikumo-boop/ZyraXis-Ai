from typing import Optional, Dict, Any

try:
    from supabase import create_client
except ImportError:
    create_client = None


class SubscriptionRepository:
    """
    Source of truth for user subscription tier.
    Backed by Supabase.
    """

    def __init__(self, supabase_url: str, supabase_key: str):
        if create_client is None:
            raise RuntimeError("supabase-py is required")

        self.client = create_client(supabase_url, supabase_key)

    def get_tier(self, user_id: str) -> str:
        """
        Returns subscription tier for a user.
        Defaults to 'free' if not found.
        """

        try:
            res = (
                self.client.table("subscriptions")
                .select("tier")
                .eq("user_id", user_id)
                .single()
                .execute()
            )

            data = getattr(res, "data", None)
            if not data:
                return "free"

            return data.get("tier", "free")

        except Exception:
            return "free"

    def set_tier(self, user_id: str, tier: str) -> None:
        """
        Upsert subscription tier.
        """

        try:
            self.client.table("subscriptions").upsert({
                "user_id": user_id,
                "tier": tier
            }).execute()
        except Exception:
            pass
