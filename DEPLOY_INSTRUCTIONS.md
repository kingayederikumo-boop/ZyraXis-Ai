# How to apply this — full replacement, not a patch

This is not a diff. It's the complete backend, built clean from scratch,
targeting the real Supabase schema. Every file in it is meant to exist;
nothing in your current repo should survive except `.git` itself.

## Steps

1. In your local clone of ZyraXis-Ai:
   ```
   cd ZyraXis-Ai
   git rm -rf .
   git checkout HEAD -- .gitignore   # if you have one worth keeping
   ```
   (or just delete everything in the folder except the `.git` directory
   directly in your file explorer, whichever is easier)

2. Extract this zip's contents directly into that now-empty folder.

3. **Deliberately not included, and not needed for V1:**
   - `frontend/` (the Next.js Mini App) — spec says no Mini App in V1;
     it's what broke every Vercel deployment by being built alongside
     the Python webhook in one project. If you want it back for V2,
     give it its own separate Vercel project, don't merge the build
     configs again.
   - `nginx/` — not used by the actual deploy targets (Vercel + Railway),
     was dead weight from an earlier deployment approach.
   - `handlers/`, `app/transport/`, old `app/bot/commands.py`/`menus.py`/
     `telegram_bot.py`/`webhook_setup.py`, `app/workers/worker.py`/
     `entrypoint.py`/`billing_worker.py`/`chat_worker.py` — all confirmed
     dead/orphaned earlier in this project, never reachable from the live
     pipeline.
   - The parallel `app/core/idempotency.py`/`retry_policy.py`/`dlq_replay.py`/
     `correlation.py`, `app/gateway/audit.py`/`rate_limiter.py`,
     `app/premium.py`, `app/repositories/`, `app/services/billing.py` etc.
     stack that appeared in your repo from a separate process — never
     wired into anything live, and building two unreconciled backends is
     exactly the failure pattern this whole project has been fighting.
     If there's real work in there worth keeping, it needs to be
     evaluated and merged deliberately, not left as a second parallel
     universe of code.

4. `git add -A && git commit -m "rebuild: complete backend against real schema, single clean stack" && git push`

5. On Railway: confirm the Custom Start Command is still
   `python -m app.workers.start_consumer` (should carry over, but verify).

6. On Vercel: this repo's `vercel.json` is Python-only now. Also check
   Settings → General → Root Directory is blank/repo-root, not `frontend`.

7. Fill in real values in `.env` (copy from `.env.example`) on both
   Vercel and Railway - same `REDIS_URL` and `DATABASE_URL` on both, or
   they'll talk to different queues/databases and nothing will work with
   no visible error.

## One bug caught during this rebuild, before it shipped

`app/main.py` called `answer_pre_checkout_query_async` from
`app/bot/telegram_client.py` - that function didn't actually exist there
until this pass. Would have crashed on the first Stars payment attempt.
Added, and it has to be a real `async def` (not the sync-wrapper pattern
the rest of that file uses) because `app/main.py` runs inside FastAPI's
own already-running event loop.

## What's still unverified (same caveats as before, unchanged by this rebuild)

- Image generation, file analysis, and video generation are built to
  documented OpenRouter API shapes but never fired against a live key
  from this environment (no network access here). Test each once for real.
- The Stars payment flow is built to Telegram's documented mechanics but
  never fired against a live bot.
- `video_jobs` has Row Level Security disabled in Supabase - every other
  table has it enabled. Your call:
  `ALTER TABLE public.video_jobs ENABLE ROW LEVEL SECURITY;`

## What's verified this pass, specifically

Every internal `app.*` import was traced to confirm the target file
exists. Every cross-file method call (`auth.*`, `gate.*`, `engine.run`,
`orchestrator.handle_message`, every `telegram_client` function, every
`payments` function, `dispatch()`'s return contract against how the
worker consumes it) was checked against its actual definition - not just
syntax-checked. This is what caught the missing
`answer_pre_checkout_query_async` above.
