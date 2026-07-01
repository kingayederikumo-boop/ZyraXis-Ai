from functools import wraps
import time

user_limits = {}

def rate_limit(max_per_day=10):
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context):
            user_id = update.effective_user.id
            now = time.time()
            # Simple in-memory; replace with DB/Ops
            if user_id not in user_limits:
                user_limits[user_id] = []
            user_limits[user_id] = [t for t in user_limits[user_id] if now - t < 86400]
            if len(user_limits[user_id]) >= max_per_day:
                await update.message.reply_text('Limit reached. Upgrade for more 👑')
                return
            user_limits[user_id].append(now)
            return await func(update, context)
        return wrapper
    return decorator

# Usage: @rate_limit() on handlers