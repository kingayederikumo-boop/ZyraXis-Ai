from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    filters,
)

from app.orchestrator.router import Orchestrator
from app.config import Config
from app.bot.payments import TelegramStarsBilling
from app.bot.commands import (
    start_command,
    help_command,
    profile_command,
    plans_command,
    stats_command,
    upgrade_command,
)
from app.services.response_router import ResponseRouter

orchestrator = Orchestrator()
billing = TelegramStarsBilling(bot_token=Config.TELEGRAM_BOT_TOKEN)
router = ResponseRouter()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    if text == '👤 Profile':
        return await profile_command(update, context)
    if text == '📊 Usage':
        return await stats_command(update, context)
    if text == '⭐ Upgrade':
        return await upgrade_command(update, context)
    if text == '❓ Help':
        return await help_command(update, context)

    result = orchestrator.handle(user_id, text)

    if isinstance(result, dict):
        status = result.get("status")

        if status == "blocked":
            await update.message.reply_text("Limit reached. Upgrade required.")
            return

        if status == "error":
            await update.message.reply_text("System error occurred.")
            return

        if status == "success":
            await update.message.reply_text(str(result.get("data")))
            return

    await update.message.reply_text(str(result))

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await billing.pre_checkout_handler(update, context)

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await billing.successful_payment_handler(update, context)

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await billing.create_stars_invoice(update, context)


# WEBHOOK MODE HANDLER
async def webhook_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_message(update, context)


def start_webhook(app):
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('profile', profile_command))
    app.add_handler(CommandHandler('plans', plans_command))
    app.add_handler(CommandHandler('stats', stats_command))
    app.add_handler(CommandHandler('upgrade', upgrade_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, webhook_handler))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/premium$'), premium_command))


def build_app():
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    start_webhook(application)
    return application
