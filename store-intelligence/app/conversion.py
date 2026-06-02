"""Correlate POS transactions with visitor sessions (±5 minute billing window)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import EventRow, SessionRow, TransactionRow
from app.models import EventType


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _format_ts(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def refresh_conversions(db: Session, store_id: str) -> int:
    """
    Mark sessions converted when a non-staff visitor was in billing within ±5 minutes
    of a POS transaction timestamp.
    """
    sessions = db.scalars(
        select(SessionRow).where(
            SessionRow.store_id == store_id,
            SessionRow.is_staff == 0,
            SessionRow.reached_billing == 1,
        )
    ).all()
    transactions = db.scalars(
        select(TransactionRow).where(TransactionRow.store_id == store_id)
    ).all()
    if not transactions:
        for session in sessions:
            if session.converted:
                session.converted = 0
                session.conversion_txn_id = None
        db.commit()
        return 0

    txn_times = [(t.transaction_id, _parse_ts(t.timestamp)) for t in transactions]
    updated = 0
    window = timedelta(minutes=5)

    for session in sessions:
        billing_events = db.scalars(
            select(EventRow)
            .where(
                EventRow.store_id == store_id,
                EventRow.visitor_id == session.visitor_id,
                EventRow.event_type.in_(
                    [EventType.ZONE_ENTER.value, EventType.BILLING_QUEUE_JOIN.value]
                ),
                EventRow.zone_id.in_(["BILLING_COUNTER", "BILLING_QUEUE"]),
                EventRow.is_staff == 0,
            )
            .order_by(EventRow.timestamp)
        ).all()

        if not billing_events:
            session.converted = 0
            session.conversion_txn_id = None
            continue

        billing_times = [_parse_ts(event.timestamp) for event in billing_events]
        matched_txn: str | None = None
        for txn_id, txn_time in txn_times:
            for billing_time in billing_times:
                if abs((txn_time - billing_time).total_seconds()) <= window.total_seconds():
                    matched_txn = txn_id
                    break
            if matched_txn:
                break

        if matched_txn:
            if not session.converted or session.conversion_txn_id != matched_txn:
                session.converted = 1
                session.conversion_txn_id = matched_txn
                updated += 1
        else:
            session.converted = 0
            session.conversion_txn_id = None

    db.commit()
    return updated
