from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    filters,
)

from app.orchestrator.router import Orchestrator
from app.config import Config
from app.bot.payments import TelegramStarsBilling

orchestrator = Orchestrator()
billing = TelegramStarsBilling(bot_token=Config.TELEGRAM_BOT_TOKEN)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    response = orchestrator.handle(user_id, text)
    await update.message.reply_text(response)


# PAYMENT FLOW
async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await billing.pre_checkout_handler(update, context)


async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await billing.successful_payment_handler(update, context)


async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger premium purchase flow."""
    await billing.create_stars_invoice(update, context)


def start():
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # Core AI handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Monetization handlers (V1.1 FINAL INTEGRATION)
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))

    # Premium purchase entrypoint
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex("^/premium$"), premium_command))

    app.run_polling()
