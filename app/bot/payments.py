"""
Telegram Stars payment handling.

Flow: upgrade button -> send_invoice -> Telegram shows pay UI -> user pays
-> pre_checkout_query (must answer within 10s) -> successful_payment
(grant the tier, record the charge).

Idempotency: Telegram can redeliver updates. telegram_payment_charge_id is
the real idempotency key - payment_events.telegram_payment_id has a unique
constraint on it in the REAL production schema (this previously wrote to
an invented `payments` table that doesn't exist in the actual database -
payment_events is the real, already-hardened immutable ledger).
"""

import uuid

from app.config import Config
from app.database.session import SessionLocal
from app.database.models import PaymentEvent
from app.gateway.auth import AuthService

auth = AuthService()


def build_invoice_payload(telegram_id, tier: str) -> str:
    return f"{telegram_id}:{tier}:{uuid.uuid4().hex[:8]}"


def parse_invoice_payload(payload: str):
    """Returns (telegram_id, tier) if payload is well-formed and tier is a
    real paid tier, else None."""
    parts = (payload or "").split(":")
    if len(parts) != 3:
        return None

    telegram_id, tier, _nonce = parts

    if tier not in Config.VALID_TIERS or tier == "free":
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
    """Grants the tier and records the charge in payment_events (the real
    ledger - constrained to tier IN ('pro','expert'), stars > 0). Returns
    (telegram_id, tier) on success, or None if the payload was bad, stars
    was missing, or this charge was already processed (redelivered update
    - don't double-grant)."""
    if not charge_id or is_payment_processed(charge_id):
        return None

    parsed = parse_invoice_payload(invoice_payload)
    if not parsed:
        print(f"Unparseable payment payload: {invoice_payload}")
        return None

    telegram_id, tier = parsed

    if not stars or stars <= 0:
        print(f"Missing/invalid stars amount for charge {charge_id}")
        return None

    tid = int(telegram_id)

    auth.get_or_create_user(telegram_id)
    auth.set_tier(telegram_id, tier, stars_paid=stars)  # writes users.tier + subscriptions row

    db = SessionLocal()
    try:
        db.add(PaymentEvent(
            telegram_payment_id=charge_id,
            telegram_id=tid,
            tier=tier,
            stars=stars,
        ))
        db.commit()
    finally:
        db.close()

    return telegram_id, tier
