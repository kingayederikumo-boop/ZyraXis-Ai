"""Telegram Stars payment handling.

Flow: upgrade button -> send_invoice -> Telegram payment UI -> pre-checkout
-> successful_payment -> validate exact tier price -> grant tier -> record.

Idempotency uses Telegram's telegram_payment_charge_id, which is uniquely
constrained in payment_events.
"""

import uuid

from app.config import Config
from app.database.session import SessionLocal
from app.database.models import PaymentEvent
from app.gateway.auth import AuthService

auth = AuthService()


def build_invoice_payload(telegram_id, tier: str) -> str:
    if tier not in Config.TIER_PRICE_STARS:
        raise ValueError(f"Invalid paid tier: {tier}")
    return f"{telegram_id}:{tier}:{uuid.uuid4().hex[:8]}"


def parse_invoice_payload(payload: str):
    """Return (telegram_id, tier) only for a valid paid tier."""
    parts = (payload or "").split(":")
    if len(parts) != 3:
        return None

    telegram_id, tier, _nonce = parts
    if tier not in Config.TIER_PRICE_STARS:
        return None

    try:
        int(telegram_id)
    except (TypeError, ValueError):
        return None

    return telegram_id, tier


def is_payment_processed(charge_id: str) -> bool:
    db = SessionLocal()
    try:
        return db.query(PaymentEvent).filter(
            PaymentEvent.telegram_payment_id == charge_id
        ).first() is not None
    finally:
        db.close()


def finalize_payment(charge_id: str, invoice_payload: str, stars: int = None):
    """Grant a paid tier only when the Telegram charge amount exactly
    matches the server-side price for the tier encoded in the payload.

    This prevents a forged/stale payload or mismatched amount from granting
    a more expensive tier for a cheaper payment.
    """
    if not charge_id or is_payment_processed(charge_id):
        return None

    parsed = parse_invoice_payload(invoice_payload)
    if not parsed:
        print(f"Unparseable payment payload: {invoice_payload}")
        return None

    telegram_id, tier = parsed
    expected_stars = Config.TIER_PRICE_STARS[tier]

    if stars is None or int(stars) != expected_stars:
        print(
            f"Payment amount mismatch for charge {charge_id}: "
            f"tier={tier}, expected={expected_stars}, received={stars}"
        )
        return None

    tid = int(telegram_id)
    auth.get_or_create_user(telegram_id)
    auth.set_tier(telegram_id, tier, stars_paid=expected_stars)

    db = SessionLocal()
    try:
        db.add(PaymentEvent(
            telegram_payment_id=charge_id,
            telegram_id=tid,
            tier=tier,
            stars=expected_stars,
        ))
        db.commit()
    finally:
        db.close()

    return telegram_id, tier
