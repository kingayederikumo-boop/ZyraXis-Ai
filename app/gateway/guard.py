from app.gateway.rate_limiter import RateLimiter
from app.config import Config

limiter = RateLimiter()

class Gatekeeper:
    """Central enforcement layer for ZyraXis requests."""

    def can_use_ai(self, user_id: str, is_premium: bool) -> bool:
        limit = Config.PREMIUM_AI_LIMIT if is_premium else Config.FREE_AI_LIMIT
        return limiter.can_use(user_id, "ai", limit)

    def can_use_roleplay(self, user_id: str, is_premium: bool) -> bool:
        limit = Config.PREMIUM_ROLEPLAY_LIMIT if is_premium else Config.FREE_ROLEPLAY_LIMIT
        return limiter.can_use(user_id, "roleplay", limit)

    def can_use_image(self, user_id: str, is_premium: bool) -> bool:
        limit = Config.PREMIUM_IMAGE_LIMIT if is_premium else Config.FREE_IMAGE_LIMIT
        return limiter.can_use(user_id, "image", limit)

    def can_use_file(self, user_id: str, is_premium: bool) -> bool:
        limit = Config.PREMIUM_FILE_LIMIT if is_premium else Config.FREE_FILE_LIMIT
        return limiter.can_use(user_id, "file", limit)

    def resolve_tier(self, user: dict | None) -> bool:
        """Basic tier resolver (placeholder for subscription system)."""
        if not user:
            return False
        return user.get("is_premium", False)
