from telegram import LabeledPrice, Update
from telegram.ext import ContextTypes
from app.config import Config

# Telegram Stars uses currency code: XTR
STARS_CURRENCY = "XTR"

class TelegramStarsBilling:
    """Handles Telegram Stars payments for premium unlocks."""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    async def create_stars_invoice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a Stars invoice to user for premium upgrade."""
        chat_id = update.effective_chat.id

        prices = [
            LabeledPrice(label="ZyraXis Premium Access", amount=100)  # Stars units
        ]

        await context.bot.send_invoice(
            chat_id=chat_id,
            title="ZyraXis Premium",
            description="Unlock premium AI limits and features",
            payload="zyraxis_premium_upgrade",
            provider_token="",  # Telegram Stars does not require provider token
            currency=STARS_CURRENCY,
            prices=prices,
            start_parameter="zyraxis-premium"
        )

    async def pre_checkout_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Must approve checkout requests from Telegram."""
        query = update.pre_checkout_query
        await query.answer(ok=True)

    async def successful_payment_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Triggered when payment is completed."""
        payment = update.message.successful_payment
        user_id = update.effective_user.id

        # Here we would upgrade user tier in DB
        print(f"Payment successful for user {user_id}: {payment}")
