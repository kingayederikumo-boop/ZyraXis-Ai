from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    filters,
)

from app.config import Config
from app.core.queue import Queue
from app.bot.commands import (
    start_command,
    help_command,
    profile_command,
    plans_command,
    stats_command,
    upgrade_command,
)
from app.bot.payments import TelegramStarsBilling

billing = TelegramStarsBilling(bot_token=Config.TELEGRAM_BOT_TOKEN)
queue = Queue()
CHANNEL = "zyraxis_jobs"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    ui_map = {
        "👤 Profile": profile_command,
        "📊 Usage": stats_command,
        "⭐ Upgrade": upgrade_command,
        "❓ Help": help_command,
    }

    if text in ui_map:
        return await ui_map[text](update, context)

    queue.push(CHANNEL, {
        "user_id": user_id,
        "text": text
    })

    await update.message.reply_text("Request queued.")


async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await billing.pre_checkout_handler(update, context)


async def payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await billing.successful_payment_handler(update, context)


def start_polling():
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("plans", plans_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("upgrade", upgrade_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success))

    app.run_polling()
