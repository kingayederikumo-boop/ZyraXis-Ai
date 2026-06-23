from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from app.orchestrator.router import Orchestrator
from app.config import Config

orchestrator = Orchestrator()

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    response = orchestrator.handle_message(user_message)

    await update.message.reply_text(response)

def start_bot():
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()
