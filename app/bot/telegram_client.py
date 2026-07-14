"""
Async-native wrapper around python-telegram-bot's Bot class.

This satisfies the spec's "python-telegram-bot (Async)" stack requirement
WITHOUT reintroducing PTB's Application/webhook dispatcher, which
docs/PRODUCTION_LOCK.md explicitly forbids ("Do not reintroduce PTB webhook
execution"). Bot is just an API client here - it sends messages and chat
actions, called from inside the existing Redis-worker loop. No PTB
Application, no PTB-managed webhook, no PTB dispatch/handler system.

FIXED (production bug): every function here used to wrap its single call
in its own asyncio.run(), creating and tearing down a brand new event loop
per message. The Bot object (and its underlying httpx connection pool) is
a long-lived singleton shared across all of those short-lived loops - each
torn-down loop left connections it had opened without properly releasing
them back to the pool. Under real traffic this manifested as:

    Pool timeout: All connections in the connection pool are occupied.

The fix is architectural, not a bigger pool: every function here is now a
plain `async def` with no internal asyncio.run() at all. The worker
(app/workers/telegram_consumer_v2.py) now runs its whole loop inside ONE
asyncio.run() call for the entire process lifetime, so the Bot's
connection pool is created once, in one loop, and reused correctly for as
long as the worker runs.
"""

import base64
import io
from telegram import Bot, LabeledPrice
from telegram.constants import ChatAction

from app.config import Config

_bot = None


def get_bot() -> Bot:
    global _bot
    if _bot is None:
        if not Config.TELEGRAM_BOT_TOKEN:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
        _bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    return _bot


async def send_message(chat_id: str, text: str, reply_markup=None):
    try:
        await get_bot().send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    except Exception as e:
        print(f"Telegram send failed: {e}")


async def send_chat_action(chat_id: str, action=ChatAction.TYPING):
    try:
        await get_bot().send_chat_action(chat_id=chat_id, action=action)
    except Exception as e:
        print(f"Chat action failed: {e}")


async def send_photo(chat_id: str, photo, caption: str = None):
    """`photo` comes from OpenRouterClient.generate_image(), which returns
    either a URL string or a base64-encoded string depending on the model/
    provider. PTB's send_photo accepts a URL directly; base64 needs
    decoding into bytes first."""
    try:
        if isinstance(photo, str) and photo.startswith("http"):
            media = photo
        elif isinstance(photo, str):
            media = io.BytesIO(base64.b64decode(photo))
        else:
            media = io.BytesIO(photo)

        await get_bot().send_photo(chat_id=chat_id, photo=media, caption=caption)
    except Exception as e:
        print(f"Photo send failed: {e}")


async def send_video(chat_id: str, video_bytes: bytes, caption: str = None):
    try:
        await get_bot().send_video(chat_id=chat_id, video=io.BytesIO(video_bytes), caption=caption)
    except Exception as e:
        print(f"Video send failed: {e}")


async def get_file_bytes(file_id: str) -> bytes:
    """Downloads a Telegram-hosted file (document/photo upload) into
    memory. Telegram only gives you a file_id in the update - you have to
    separately call getFile to resolve it to a path, then download it.

    NOT verified against a live call from here (no network access in this
    environment). File.download_as_bytearray() is PTB's documented method
    for pulling file contents into memory as of the 20.x/21.x line -
    confirm against python-telegram-bot==21.9 specifically if this errors,
    method names have moved around across PTB major versions before."""
    file = await get_bot().get_file(file_id)
    return bytes(await file.download_as_bytearray())


async def answer_callback_query(callback_query_id: str, text: str = None):
    """Stops the loading spinner on an inline button. Must be called for
    every callback_query, even ones we don't otherwise act on, or the
    button spins indefinitely on the user's screen."""
    try:
        await get_bot().answer_callback_query(callback_query_id, text=text)
    except Exception as e:
        print(f"Callback answer failed: {e}")


async def answer_pre_checkout_query_async(pre_checkout_query_id: str, ok: bool, error_message: str = None):
    """Called directly from app/main.py's webhook handler, not from the
    worker - must complete within Telegram's 10-second SLA, which queueing
    it through Redis (an earlier version did this) has no bound on."""
    await get_bot().answer_pre_checkout_query(pre_checkout_query_id, ok=ok, error_message=error_message)


async def send_invoice(chat_id: str, title: str, description: str, payload: str,
                        amount: int, label: str, currency: str = "XTR"):
    """Telegram Stars invoice. provider_token is deliberately empty - Stars
    payments don't use a payment provider, Telegram handles them natively.
    XTR requires exactly one price component (Telegram's rule, not ours)."""
    try:
        await get_bot().send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",
            currency=currency,
            prices=[LabeledPrice(label, amount)],
        )
    except Exception as e:
        print(f"Invoice send failed: {e}")