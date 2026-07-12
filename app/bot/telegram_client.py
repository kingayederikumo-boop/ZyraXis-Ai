"""
Thin sync wrapper around python-telegram-bot's Bot class.

This satisfies the spec's "python-telegram-bot (Async)" stack requirement
WITHOUT reintroducing PTB's Application/webhook dispatcher, which
docs/PRODUCTION_LOCK.md explicitly forbids ("Do not reintroduce PTB webhook
execution"). Bot is just an API client here - it sends messages and chat
actions, called from inside the existing Redis-worker loop. No PTB
Application, no PTB-managed webhook, no PTB dispatch/handler system.

Known limitation (MVP, flagged not hidden): each call opens a fresh event
loop via asyncio.run(). Fine at current volume. If the worker becomes a
bottleneck, this should move to one persistent event loop per worker
process instead of one per message.
"""

import asyncio
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


def send_message(chat_id: str, text: str, reply_markup=None):
    async def _send():
        await get_bot().send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    try:
        asyncio.run(_send())
    except Exception as e:
        print(f"Telegram send failed: {e}")


def send_chat_action(chat_id: str, action=ChatAction.TYPING):
    async def _send():
        await get_bot().send_chat_action(chat_id=chat_id, action=action)

    try:
        asyncio.run(_send())
    except Exception as e:
        print(f"Chat action failed: {e}")


def send_photo(chat_id: str, photo, caption: str = None):
    """`photo` comes from OpenRouterClient.generate_image(), which returns
    either a URL string or a base64-encoded string depending on the model/
    provider (see app/providers/openrouter.py docstring - unverified against
    a live call). PTB's send_photo accepts a URL directly; base64 needs
    decoding into bytes first. This mismatch (code assumed raw bytes) was
    caught here before it could crash on the first real image request."""
    async def _send():
        if isinstance(photo, str) and photo.startswith("http"):
            media = photo
        elif isinstance(photo, str):
            import base64
            media = io.BytesIO(base64.b64decode(photo))
        else:
            media = io.BytesIO(photo)

        await get_bot().send_photo(chat_id=chat_id, photo=media, caption=caption)

    try:
        asyncio.run(_send())
    except Exception as e:
        print(f"Photo send failed: {e}")


def send_video(chat_id: str, video_bytes: bytes, caption: str = None):
    async def _send():
        await get_bot().send_video(chat_id=chat_id, video=io.BytesIO(video_bytes), caption=caption)

    try:
        asyncio.run(_send())
    except Exception as e:
        print(f"Video send failed: {e}")


def get_file_bytes(file_id: str) -> bytes:
    """Downloads a Telegram-hosted file (document/photo upload) into
    memory. Telegram only gives you a file_id in the update - you have to
    separately call getFile to resolve it to a path, then download it.
    This was the missing piece blocking /analyze entirely: the webhook
    only ever forwarded update JSON, never fetched the actual file.

    NOT verified against a live call from here (no network access in this
    environment). File.download_as_bytearray() is PTB's documented method
    for pulling file contents into memory as of the 20.x/21.x line, but
    confirm against python-telegram-bot==21.9 specifically (pinned in
    requirements.txt) before relying on this - method names have moved
    around across PTB major versions before."""
    async def _get():
        file = await get_bot().get_file(file_id)
        return bytes(await file.download_as_bytearray())

    return asyncio.run(_get())


def answer_callback_query(callback_query_id: str, text: str = None):
    """Stops the loading spinner on an inline button. Must be called for
    every callback_query, even ones we don't otherwise act on, or the
    button spins indefinitely on the user's screen."""
    async def _answer():
        await get_bot().answer_callback_query(callback_query_id, text=text)

    try:
        asyncio.run(_answer())
    except Exception as e:
        print(f"Callback answer failed: {e}")


async def answer_pre_checkout_query_async(pre_checkout_query_id: str, ok: bool, error_message: str = None):
    """Genuinely async (not the sync-wrapper pattern the rest of this file
    uses) because app/main.py calls this from inside FastAPI's own already-
    running event loop - asyncio.run() cannot be called from within an
    event loop that's already running, it would raise RuntimeError."""
    await get_bot().answer_pre_checkout_query(pre_checkout_query_id, ok=ok, error_message=error_message)


def send_invoice(chat_id: str, title: str, description: str, payload: str,
                  amount: int, label: str, currency: str = "XTR"):
    """Telegram Stars invoice. provider_token is deliberately empty - Stars
    payments don't use a payment provider, Telegram handles them natively.
    XTR requires exactly one price component (Telegram's rule, not ours)."""
    async def _send():
        await get_bot().send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",
            currency=currency,
            prices=[LabeledPrice(label, amount)],
        )

    try:
        asyncio.run(_send())
    except Exception as e:
        print(f"Invoice send failed: {e}")


async def answer_pre_checkout_query_async(pre_checkout_query_id: str, ok: bool, error_message: str = None):
    """Async-native, for use directly inside app/main.py's webhook handler
    (which is already running inside FastAPI's event loop - the sync
    wrapper pattern used everywhere else in this file would fail there
    with 'asyncio.run() cannot be called from a running event loop').

    This MUST be called within 10 seconds of the pre_checkout_query
    arriving or Telegram fails the payment. That's exactly why this
    bypasses the Redis queue entirely and is called straight from the
    webhook - queuing it (as an earlier version of this file did) meant
    the answer's timing depended on queue depth, which has no bound.
    Answering directly in the webhook removes that dependency."""
    await get_bot().answer_pre_checkout_query(pre_checkout_query_id, ok=ok, error_message=error_message)
