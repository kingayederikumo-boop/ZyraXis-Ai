# ZyraXis AI

Telegram-native AI assistant. Chat, roleplay, coding help, web search,
image and video generation, file analysis — free/pro/expert tiers billed
via Telegram Stars. See `docs/PRODUCTION_LOCK.md` for the architecture
rules before changing anything structural.

## Architecture

```
Telegram --> /webhook (Vercel, app/main.py) --> Redis (Upstash) queue
                                                        |
                                                        v
                                    Worker (Railway, app/workers/start_consumer.py)
                                                        |
                                                        v
                                    Orchestrator -> OpenRouter / Supabase
```

Two separate deploy targets, both from this one repo:
- **Vercel**: the webhook only (`app/main.py`). No frontend build — see
  `vercel.json`, it's Python-only on purpose.
- **Railway** (or any always-on host): the worker
  (`python -m app.workers.start_consumer`). This cannot run on Vercel —
  it's a persistent loop, Vercel functions are request-triggered.

Both must point at the **same** `REDIS_URL` and `DATABASE_URL`, or the
webhook and worker end up talking to different queues/databases and
nothing will appear to work, with no error anywhere.

## Environment variables

See `.env.example`. Required: `TELEGRAM_BOT_TOKEN`, `OPENROUTER_API_KEY`,
`DATABASE_URL`, `REDIS_URL`, `WEBHOOK_URL`. Optional: per-feature
OpenRouter keys (`OPENROUTER_API_KEY_CHAT`/`_IMAGE`/etc.) for independent
spend caps, `OPENROUTER_MODEL_CHAIN` for fallback routing.

## Local development

```
pip install -r requirements.txt --break-system-packages
cp .env.example .env   # fill in real values
python app/main.py     # webhook, local
python -m app.workers.start_consumer   # worker, separate terminal
```

## Database migrations

Alembic, pointed at `Config.DATABASE_URL` via `migrations/env.py`. The
production database is already at the schema `migrations/versions/`
describes — run `alembic stamp head`, not `upgrade head`, against it.
Only use `upgrade head` against a genuinely fresh database.

## Deploying

1. Push to `main`.
2. Vercel redeploys the webhook automatically on push.
3. Redeploy the worker on Railway (redeploy on push if connected, or
   manually otherwise).
4. `WEBHOOK_URL` in env vars must match Vercel's actual production URL —
   the webhook self-registers with Telegram on every boot using this
   value, no manual `setWebhook` call needed.

## Commands

`/start /help /menu /usage /premium /chat /roleplay /exitroleplay
/analyze /image /video /search /code` — public. `/admin /premiumadd
/premiumremove` — restricted to `users.is_admin = true`, deliberately not
registered in BotFather's public command list.
