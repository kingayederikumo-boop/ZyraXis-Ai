from app.providers.openrouter import OpenRouterClient
from app.gateway.guard import Gatekeeper, FEATURE_TO_DB_EVENT
from app.gateway.auth import AuthService
from app.database.session import SessionLocal
from app.database.models import UsageEvent, ConversationMessage
from app.ops.logger import OpsLogger
from app.core.engine import ExecutionEngine

auth = AuthService()
gate = Gatekeeper()
logger = OpsLogger()
engine = ExecutionEngine()


MEMORY_FEATURES = {"chat", "roleplay", "code"}
HISTORY_LIMIT = 20  # last 20 messages = 10 exchanges


def _fetch_history(db, telegram_id, feature):
    rows = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.telegram_id == telegram_id, ConversationMessage.feature == feature)
        .order_by(ConversationMessage.created_at.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    rows.reverse()
    return [{"role": r.role, "content": r.content} for r in rows]


def _usage_warning(tid: int, tier: str, feature: str) -> str | None:
    """Spec requires exact quota numbers stay hidden during normal use,
    except at 80% and 100% thresholds - this computes that, called after
    the usage_events row for this request is already committed, so the
    percentage reflects the request that just happened."""
    db_feature = FEATURE_TO_DB_EVENT.get(feature, "chat")
    limit = gate._limit(tier, db_feature)
    if not limit:
        return None

    used = gate._usage_today(tid, db_feature)
    pct = int(used / limit * 100)

    if pct >= 100:
        return f"\n\n_You've used 100% of today's {feature} quota - resets tomorrow._"
    if pct >= 80:
        return f"\n\n_Heads up: {pct}% of today's {feature} quota used._"
    return None


class Orchestrator:
    """V1 production orchestrator, tier and mode aware. Reads/writes the
    REAL schema: feature_limits for quotas, usage_events (one row per
    use) for consumption - not a hardcoded limits dict or a per-day counter
    column, neither of which exist in the actual database."""

    def handle_message(self, telegram_id: str, text: str, feature: str = "chat", context: dict | None = None):
        try:
            user = auth.get_or_create_user(telegram_id)
            tier = user.tier
            tid = int(telegram_id)

            # If this is a plain message (feature left as default "chat")
            # and the user is in a non-chat mode (e.g. roleplay via /roleplay),
            # route it through that mode instead. Explicit feature args
            # (e.g. from /image, /search) always win.
            if feature == "chat" and user.current_mode != "chat":
                feature = user.current_mode

            logger.event("request_received", telegram_id, {"text_length": len(text), "feature": feature})

            if not gate.can_use(tid, tier, feature):
                logger.event("quota_denied", telegram_id, {"feature": feature, "tier": tier})
                return {"status": "blocked", "tier": tier, "feature": feature}

            run_context = dict(context or {})
            if feature in MEMORY_FEATURES:
                db = SessionLocal()
                try:
                    run_context["history"] = _fetch_history(db, tid, feature)
                finally:
                    db.close()

            try:
                response = engine.run(feature, text, context=run_context)
            except NotImplementedError:
                return {"status": "unsupported", "feature": feature}
            except Exception as e:
                logger.error("ai_error", telegram_id, str(e))
                return {"status": "error"}

            db = SessionLocal()
            try:
                db.add(UsageEvent(telegram_id=tid, feature=FEATURE_TO_DB_EVENT.get(feature, "chat")))
                db.commit()
            finally:
                db.close()

            logger.event("ai_success", telegram_id, {"feature": feature})

            if feature in MEMORY_FEATURES:
                db = SessionLocal()
                try:
                    db.add(ConversationMessage(telegram_id=tid, feature=feature, role="user", content=text))
                    db.add(ConversationMessage(telegram_id=tid, feature=feature, role="assistant", content=response))
                    db.commit()
                finally:
                    db.close()

            # FIX: spec requires 80%/100% usage warnings to appear
            # automatically during normal use, not only via /usage - this
            # wasn't built before. Only applied to plain-text responses
            # (chat/roleplay/code/search) - appending text to an image URL
            # or a video job dict wouldn't make sense.
            if feature in ("chat", "roleplay", "code", "search") and isinstance(response, str):
                warning = _usage_warning(tid, tier, feature)
                if warning:
                    response = response + warning

            return {"status": "success", "data": response, "feature": feature}

        except Exception as e:
            logger.error("orchestrator_error", telegram_id, str(e))
            return {"status": "error"}
