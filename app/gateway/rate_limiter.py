from app.config import Config

class RateLimiter:

    def can_use_ai(self, usage):
        return usage.ai_requests < Config.FREE_DAILY_LIMIT
