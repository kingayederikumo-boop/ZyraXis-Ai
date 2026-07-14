import os
import json
import time
import asyncio
import redis
from telegram.constants import ChatAction

from app.orchestrator.router import Orchestrator
from app.queue.dlq import push_dlq, push_retry
from app.monitoring.heartbeat import start_heartbeat
from app.bot.telegram_client import (
    send_message, send_chat_action, answer_callback_query, send_photo, send_video,
    send_invoice, get_file_bytes,
)
from app.bot.dispatch import dispatch, CALLBACK_COMMANDS
from app.bot.payments import build_invoice_payload, finalize_payment
from app.config import Config
from app.database.session import SessionLocal
from app.database.models import VideoJob
from app.core.engine import video_client

QUEUE_NAME = "telegram_updates"
VIDEO_POLL_INTERVAL_SECONDS = 30

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)
orchestrator = Orchestrator()

_last_video_poll = 0.0


async def process_callback_query(callback_query: dict):
    """Inline button taps arrive as a different update type than messages -
    this was previously unhandled entirely, so every button tap did nothing."""
    callback_id = callback_query.get("id")
    data = callback_query.get("data", "")
    message = callback_query.get("message", {})
    chat = message.get("chat", {})
    chat_id = str(chat.get("id"))
    from_ = callback_query.get("from", {})
    user_id = str(from_.get("id", ""))

    if data.startswith("upgrade:"):
        tier = data.split(":", 1)[1]

        if tier not in Config.VALID_TIERS or tier == "free":
            await answer_callback_query(callback_id, text="Invalid plan")
            return

        await answer_callback_query(callback_id)

        price = Config.TIER_PRICE_STARS[tier]
        await send_invoice(
            chat_id,
            title=f"ZyraXis {tier.capitalize()}",
            description=f"Upgrade to {tier.capitalize()} — {price} Stars",
            payload=build_invoice_payload(user_id, tier),
            amount=price,
            label=tier.capitalize(),
        )
        return

    handler = CALLBACK_COMMANDS.get(data)
    if handler:
        await answer_callback_query(callback_id)
        reply_text, reply_markup = handler(user_id)
        await send_message(chat_id, reply_text, reply_markup=reply_markup)
        return

    # Feature buttons not yet mapped here (settings, etc.)
    await answer_callback_query(callback_id, text="Not available yet")
    await send_message(chat_id, "That feature isn't wired up yet — coming soon.")


async def process_successful_payment(message: dict):
    payment = message.get("successful_payment", {})
    chat = message.get("chat", {})
    chat_id = str(chat.get("id"))

    result = finalize_payment(
        payment.get("telegram_payment_charge_id"),
        payment.get("invoice_payload", ""),
        payment.get("total_amount"),
    )

    if result is None:
        return

    telegram_id, tier = result
    await send_message(
        chat_id,
        f"✅ You're now on {tier.capitalize()}! Thanks for upgrading.\n\n"
        f"Use /premium anytime to check your plan."
    )


async def process_document(message: dict, user_id: str, chat_id: str):
    """A document upload is treated as an /analyze request automatically -
    the caption (if any) is the question, otherwise a sensible default."""
    document = message.get("document", {})
    file_id = document.get("file_id")
    filename = document.get("file_name", "file")
    prompt = message.get("caption") or "Summarize this document."

    if not file_id:
        return

    await send_chat_action(chat_id, ChatAction.UPLOAD_DOCUMENT)

    try:
        file_bytes = await get_file_bytes(file_id)
    except Exception as e:
        await send_message(chat_id, "Couldn't download that file. Try sending it again.")
        print(f"File download failed: {e}")
        return

    # Orchestrator/DB/OpenRouter calls are synchronous (SQLAlchemy, requests)
    # - fine to call directly inline here. This worker processes one message
    # at a time anyway (no concurrency to protect), so a blocking call just
    # means "wait before the next await," identical to before this rewrite.
    outcome = orchestrator.handle_message(
        user_id, prompt, feature="file",
        context={"file_bytes": file_bytes, "filename": filename},
    )
    await _send_outcome(chat_id, outcome)


async def process_event(event: dict):
    try:
        payload = event.get("payload", {})

        if "callback_query" in payload:
            await process_callback_query(payload["callback_query"])
            return

        message = payload.get("message", {})

        if "successful_payment" in message:
            await process_successful_payment(message)
            return

        chat = message.get("chat", {})
        from_ = message.get("from", {})

        chat_id = str(chat.get("id"))
        user_id = str(from_.get("id", ""))
        first_name = from_.get("first_name")

        if not chat_id:
            return

        if "document" in message:
            await process_document(message, user_id, chat_id)
            return

        text = message.get("text", "")
        if not text:
            return

        if text.startswith("/"):
            result = dispatch(text, user_id, first_name=first_name)

            if result is not None:
                kind = result[0]

                if kind == "canned":
                    _, reply_text, reply_markup = result
                    await send_message(chat_id, reply_text, reply_markup=reply_markup)
                    return

                if kind == "invalid":
                    _, error_text = result
                    await send_message(chat_id, error_text)
                    return

                if kind == "orchestrate":
                    _, feature, args = result
                    await send_chat_action(chat_id, ChatAction.TYPING)
                    outcome = orchestrator.handle_message(user_id, args, feature=feature)
                    await _send_outcome(chat_id, outcome, chat_id_for_video=chat_id, telegram_id_for_video=user_id)
                    return

                await send_message(chat_id, "Something went wrong handling that command.")
                return

        await send_chat_action(chat_id, ChatAction.TYPING)

        result = orchestrator.handle_message(user_id, text)
        await _send_outcome(chat_id, result)

    except Exception as e:
        err = str(e)

        if "timeout" in err.lower() or "redis" in err.lower():
            push_retry(event)
        else:
            push_dlq(event, err)

        print(f"Processing failed: {e}")


async def _send_outcome(chat_id: str, result, chat_id_for_video: str = None, telegram_id_for_video: str = None):
    """Shared by plain-text chat and orchestrated commands (/image, /search,
    /code, /video, uploaded documents) so all get identical quota/error/
    success handling."""
    if not isinstance(result, dict):
        await send_message(chat_id, str(result))
        return

    status = result.get("status")

    if status == "blocked":
        tier = result.get("tier", "free")
        if tier == "free":
            await send_message(
                chat_id,
                "You've reached today's free AI limit.\n\n"
                "Continue with Pro and unlock:\n"
                "• More AI conversations\n"
                "• Better reasoning\n"
                "• Smarter web search\n"
                "• Video generation\n"
                "• Faster responses\n\n"
                "Use /premium to upgrade — 200 ⭐"
            )
        else:
            await send_message(chat_id, "Today's limit reached for this tier. It resets daily.")
        return

    if status == "error":
        await send_message(chat_id, "Something went wrong on my end. Try again in a moment.")
        return

    if status == "unsupported":
        await send_message(chat_id, "That feature isn't available yet — coming soon.")
        return

    if status == "success":
        feature = result.get("feature")

        if feature == "image":
            await send_photo(chat_id, result.get("data"))
            return

        if feature == "video":
            # data here is the job dict from submit_video(), not a finished
            # video - it takes 30s-minutes. Record it and tell the user;
            # the polling loop in run() delivers it later.
            job = result.get("data") or {}
            job_id = job.get("id")
            polling_url = job.get("polling_url")

            if not job_id or not polling_url:
                await send_message(chat_id, "Video job couldn't be started. Try again in a moment.")
                return

            db = SessionLocal()
            try:
                db.add(VideoJob(
                    telegram_id=telegram_id_for_video,
                    chat_id=chat_id_for_video or chat_id,
                    job_id=job_id,
                    polling_url=polling_url,
                    status="pending",
                ))
                db.commit()
            finally:
                db.close()

            await send_message(
                chat_id,
                "🎬 Your video is being generated - this usually takes a minute or two. "
                "I'll send it here as soon as it's ready."
            )
            return

        await send_message(chat_id, str(result.get("data")))
        return

    await send_message(chat_id, str(result))


async def poll_pending_videos():
    """Runs roughly every VIDEO_POLL_INTERVAL_SECONDS from inside the main
    loop below - not on every iteration, since that would hit OpenRouter
    every ~5s per pending job for something that takes minutes."""
    global _last_video_poll

    now = time.time()
    if now - _last_video_poll < VIDEO_POLL_INTERVAL_SECONDS:
        return
    _last_video_poll = now

    db = SessionLocal()
    try:
        pending = db.query(VideoJob).filter(VideoJob.status == "pending").all()
        jobs = [(j.id, j.chat_id, j.polling_url) for j in pending]
    finally:
        db.close()

    for job_row_id, chat_id, polling_url in jobs:
        try:
            status_data = video_client.poll_video(polling_url)
        except Exception as e:
            print(f"Video poll failed for job {job_row_id}: {e}")
            continue

        status = status_data.get("status")

        if status == "completed":
            urls = status_data.get("unsigned_urls") or []
            if urls:
                try:
                    video_bytes = video_client.download_video(urls[0])
                    await send_video(chat_id, video_bytes)
                except Exception as e:
                    await send_message(chat_id, "Your video finished but couldn't be delivered. Contact support.")
                    print(f"Video download/send failed: {e}")
            else:
                await send_message(chat_id, "Video finished but no output was returned. Contact support.")
            _set_video_job_status(job_row_id, "completed")

        elif status in ("failed", "cancelled", "expired"):
            await send_message(chat_id, f"Video generation didn't complete ({status}). Try /video again.")
            _set_video_job_status(job_row_id, status)

        # else: still pending - leave it, check again next interval


def _set_video_job_status(job_row_id: int, status: str):
    db = SessionLocal()
    try:
        job = db.query(VideoJob).filter(VideoJob.id == job_row_id).first()
        if job:
            job.status = status
            db.commit()
    finally:
        db.close()


async def run():
    """FIX: this whole function is now async and runs inside exactly ONE
    asyncio.run() call for the entire process lifetime (see start_consumer.py
    / __main__ below). Previously every individual Telegram API call opened
    and closed its own event loop - the Bot's shared httpx connection pool
    doesn't tolerate that and eventually exhausted itself
    ("Pool timeout: All connections in the connection pool are occupied").
    redis_client.brpop() is a blocking synchronous call - that's fine here,
    since this worker processes exactly one message at a time anyway; it
    just pauses this coroutine, it doesn't need to run concurrently with
    anything else."""
    print("Telegram consumer v2 started...")

    start_heartbeat()

    while True:
        try:
            item = redis_client.brpop(QUEUE_NAME, timeout=5)

            if item:
                _, raw = item
                event = json.loads(raw)
                await process_event(event)

            # Runs whether or not a message arrived this cycle - throttled
            # internally to ~every 30s regardless of how often we get here.
            await poll_pending_videos()

        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    asyncio.run(run())