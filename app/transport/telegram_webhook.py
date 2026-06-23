from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application

from app.config import Config
from app.core.runtime import handle_user
from app.transport.webhook_manager import set_webhook

app = FastAPI()

telegram_app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()


@app.on_event("startup")
async def startup():
    await telegram_app.initialize()
    await telegram_app.start()
    set_webhook()


@app.on_event("shutdown")
async def shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    update = Update.de_json(data, telegram_app.bot)

    if update.message:
        user_id = str(update.message.from_user.id)
        text = update.message.text

        response = handle_user(user_id, text)

        await update.message.reply_text(response)

    return {"ok": True}
