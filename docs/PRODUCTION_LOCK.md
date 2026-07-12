# ZyraXis AI — Production Lock

This supersedes any earlier version of this document. It reflects the
actual, verified architecture as of this rebuild — not aspirational
design, not what an earlier draft said before the schema and billing
system were corrected against the real database.

## Ingestion — ONE path, no exceptions

Telegram → `POST /webhook` (Vercel, `app/main.py`) → push to Redis list
`telegram_updates` → worker (`app/workers/telegram_consumer_v2.py`,
hosted on Railway, run via `python -m app.workers.start_consumer`) →
pops the queue, calls the Orchestrator, replies via Telegram's API.

**Do not reintroduce python-telegram-bot's `Application`/webhook
dispatcher.** `python-telegram-bot`'s `Bot` class IS used in this
codebase (`app/bot/telegram_client.py`) — as a plain async API client for
sending messages/photos/invoices and answering callback queries. That is
not the same thing as PTB's own webhook/polling execution model, which is
what's actually forbidden. If you're not sure which one something is:
does it define its own `Application`, register `CommandHandler`s, or run
its own `run_webhook()`/`run_polling()`? If yes, it's the forbidden
pattern.

**`pre_checkout_query` is answered synchronously inside `app/main.py`'s
webhook handler, never via the queue.** Telegram gives exactly 10 seconds
to answer or the payment fails. Queue latency has no upper bound. This is
not optional.

## Database — the real schema

Supabase project `simbzoxqbuzvtgrvwmdj`. Tables: `users` (keyed on
`telegram_id` bigint, not a separate autoincrement id), `usage_events`
(one row per use — NOT a counter column), `payment_events` (immutable
Stars ledger, `telegram_payment_id` uniquely constrained — this IS the
payment idempotency guard), `subscriptions` (tier-change history),
`feature_limits` (real tier × feature daily quotas — read from here, never
hardcode limits in application config again), `event_logs`, `audit_logs`,
`video_jobs`.

If application code and this schema ever disagree, the database is right
and the code is wrong. This was gotten backwards once already.

## Billing

Three tiers: free / pro / expert. Stars pricing: pro=200, expert=1100
(`Config.TIER_PRICE_STARS`). Quotas live in `feature_limits`, not in
Python. A tier change writes both `users.tier` (fast lookup) and a
`subscriptions` row (history) — `AuthService.set_tier()` does both, always
use it rather than updating `users.tier` directly.

## Scope — V1

Native Telegram chat only. **No Mini App, no `frontend/` directory, no
Next.js build in this deployment.** Vercel serves exactly one thing:
`app/main.py` as a Python function. If a future V2 adds a Mini App, it
gets its own Vercel project — do not merge it back into this one's build
config; that exact mistake caused every deployment on this project to
fail silently for an extended period.

## Features and their real status

Chat, roleplay, coding assistant: live, via OpenRouter chat completions.
Web search: live, via OpenRouter's `openrouter:web_search` server tool.
Image generation: live, via OpenRouter's `/api/v1/images`. File analysis:
live for text/PDF/DOCX uploads. Video generation: live, genuinely
asynchronous (submit → `video_jobs` row → worker polls `/api/v1/videos`
every ~30s → delivers on completion).

None of the above were verified against a live API call as of this
rebuild — each is built to documented request/response shapes but
untested end-to-end. Test each once before considering it trustworthy.
