from telegram import LabeledPrice, Update
from telegram.ext import ContextTypes
from app.gateway.auth import AuthService

# Telegram Stars currency
STARS_CURRENCY = "XTR"

auth = AuthService()

class TelegramStarsBilling:
    """Monetization Layer V1.1 — Telegram Stars integration."""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    async def create_stars_invoice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id

        prices = [
            LabeledPrice(label="ZyraXis Premium Access", amount=100)
        ]

        await context.bot.send_invoice(
            chat_id=chat_id,
            title="ZyraXis Premium",
            description="Unlock premium AI limits and features",
            payload="zyraxis_premium_upgrade",
            provider_token="",
            currency=STARS_CURRENCY,
            prices=prices,
            start_parameter="zyraxis-premium"
        )

    async def pre_checkout_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.pre_checkout_query
        await query.answer(ok=True)

    async def successful_payment_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)

        # REAL MONETIZATION HOOK
        auth.upgrade_to_premium(user_id)

        await update.message.reply_text("Premium activated successfully.")