from app.config import Config

class Gatekeeper:
    """Central enforcement layer for ZyraXis requests (DB-source aligned)."""

    def can_use_ai(self, usage_count: int, is_premium: bool) -> bool:
        limit = Config.PREMIUM_AI_LIMIT if is_premium else Config.FREE_AI_LIMIT
        return usage_count < limit

    def can_use_roleplay(self, usage_count: int, is_premium: bool) -> bool:
        limit = Config.PREMIUM_ROLEPLAY_LIMIT if is_premium else Config.FREE_ROLEPLAY_LIMIT
        return usage_count < limit

    def can_use_image(self, usage_count: int, is_premium: bool) -> bool:
        limit = Config.PREMIUM_IMAGE_LIMIT if is_premium else Config.FREE_IMAGE_LIMIT
        return usage_count < limit

    def can_use_file(self, usage_count: int, is_premium: bool) -> bool:
        limit = Config.PREMIUM_FILE_LIMIT if is_premium else Config.FREE_FILE_LIMIT
        return usage_count < limit

    def resolve_tier(self, user: dict | None) -> bool:
        if not user:
            return False
        return bool(user.get("is_premium", False))