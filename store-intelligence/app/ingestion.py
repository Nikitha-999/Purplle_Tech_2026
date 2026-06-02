"""Event ingestion, idempotent persistence, and session materialization."""

from __future__ import annotations

import json
from datetime import timezone
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.conversion import refresh_conversions
from app.database import EventRow, SessionRow, _utc_now_iso
from app.models import Event, EventIngestError, EventIngestResponse, EventType


def _format_event_timestamp(value) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_zones(session_row: SessionRow) -> list[str]:
    try:
        zones = json.loads(session_row.zones_visited or "[]")
        return zones if isinstance(zones, list) else []
    except json.JSONDecodeError:
        return []


def _save_zones(session_row: SessionRow, zones: list[str]) -> None:
    session_row.zones_visited = json.dumps(sorted(set(zones)))


def _get_or_create_session(db: Session, event: Event) -> SessionRow:
    row = db.get(SessionRow, event.visitor_id)
    if row is None:
        from sqlalchemy import select

        row = db.scalar(select(SessionRow).where(SessionRow.visitor_id == event.visitor_id))
    if row is None:
        row = SessionRow(
            session_id=event.visitor_id,
            store_id=event.store_id,
            visitor_id=event.visitor_id,
            is_staff=1 if event.is_staff else 0,
            zones_visited="[]",
        )
        db.add(row)
    return row


def _apply_session_side_effects(db: Session, event: Event) -> None:
    session = _get_or_create_session(db, event)
    ts = _format_event_timestamp(event.timestamp)

    if event.is_staff:
        session.is_staff = 1

    if event.event_type == EventType.ENTRY:
        if not session.started_at:
            session.started_at = ts
        session.ended_at = None

    elif event.event_type == EventType.EXIT:
        session.ended_at = ts

    elif event.event_type == EventType.REENTRY:
        session.reentry_count = (session.reentry_count or 0) + 1
        session.ended_at = None
        if not session.started_at:
            session.started_at = ts

    elif event.event_type == EventType.ZONE_ENTER:
        if event.zone_id:
            zones = _load_zones(session)
            if event.zone_id not in zones:
                zones.append(event.zone_id)
            _save_zones(session, zones)
            if event.zone_id == "BILLING_COUNTER":
                session.reached_billing = 1

    elif event.event_type == EventType.BILLING_QUEUE_JOIN:
        session.reached_queue = 1

    elif event.event_type == EventType.BILLING_QUEUE_ABANDON:
        session.abandoned_queue = 1


def _event_to_row(event: Event) -> EventRow:
    return EventRow(
        event_id=event.event_id,
        store_id=event.store_id,
        camera_id=event.camera_id,
        visitor_id=event.visitor_id,
        event_type=event.event_type.value,
        timestamp=_format_event_timestamp(event.timestamp),
        zone_id=event.zone_id,
        dwell_ms=event.dwell_ms,
        is_staff=1 if event.is_staff else 0,
        confidence=event.confidence,
        metadata_json=event.metadata.model_dump_json(),
        ingested_at=_utc_now_iso(),
    )


def ingest_events(db: Session, raw_events: list[dict[str, Any]]) -> EventIngestResponse:
    accepted = 0
    duplicates = 0
    rejected = 0
    errors: list[EventIngestError] = []
    touched_stores: set[str] = set()

    for index, raw in enumerate(raw_events):
        event_id = raw.get("event_id") if isinstance(raw, dict) else None
        try:
            event = Event.model_validate(raw)
        except ValidationError as exc:
            rejected += 1
            errors.append(
                EventIngestError(
                    event_id=str(event_id) if event_id else None,
                    reason=str(exc.errors()),
                )
            )
            continue

        existing = db.get(EventRow, event.event_id)
        if existing:
            duplicates += 1
            continue

        db.add(_event_to_row(event))
        _apply_session_side_effects(db, event)
        db.flush()
        accepted += 1
        touched_stores.add(event.store_id)

    db.commit()

    for store_id in touched_stores:
        refresh_conversions(db, store_id)

    return EventIngestResponse(
        accepted=accepted,
        duplicates=duplicates,
        rejected=rejected,
        errors=errors,
    )
