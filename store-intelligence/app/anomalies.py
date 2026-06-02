"""Rule-based anomaly detection (Phase 3.9)."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import EventRow, SessionRow
from app.models import AnomalyItem, AnomalyResponse, EventType


def _day_bounds(metric_date: date) -> tuple[str, str]:
    start = datetime(metric_date.year, metric_date.month, metric_date.day, tzinfo=timezone.utc)
    end = datetime(metric_date.year, metric_date.month, metric_date.day, 23, 59, 59, tzinfo=timezone.utc)
    return (
        start.isoformat().replace("+00:00", "Z"),
        end.isoformat().replace("+00:00", "Z"),
    )


def _load_layout_zone_ids() -> list[str]:
    settings = get_settings()
    try:
        payload = json.loads(settings.layout_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    zone_ids: set[str] = set()
    for camera in payload.get("cameras", []):
        for zone in camera.get("zones", []):
            zone_id = zone.get("zone_id")
            if zone_id:
                zone_ids.add(zone_id)
    return sorted(zone_ids)


def _session_in_window(session: SessionRow, start: str, end: str) -> bool:
    if not session.started_at:
        return False
    return start <= session.started_at <= end


def compute_anomalies(db: Session, store_id: str, metric_date: date | None = None) -> AnomalyResponse:
    target = metric_date or date.today()
    start, end = _day_bounds(target)

    sessions = db.scalars(select(SessionRow).where(SessionRow.store_id == store_id)).all()
    customer_sessions = [s for s in sessions if s.is_staff == 0 and _session_in_window(s, start, end)]

    entry_count = len(customer_sessions)
    converted_count = sum(1 for s in customer_sessions if s.converted == 1)
    conversion_rate = converted_count / entry_count if entry_count else 0.0

    queue_join_count = db.scalar(
        select(func.count())
        .select_from(EventRow)
        .where(
            EventRow.store_id == store_id,
            EventRow.timestamp >= start,
            EventRow.timestamp <= end,
            EventRow.event_type == EventType.BILLING_QUEUE_JOIN.value,
            EventRow.is_staff == 0,
        )
    ) or 0

    zone_enter_rows = db.execute(
        select(EventRow.zone_id, func.count())
        .where(
            EventRow.store_id == store_id,
            EventRow.timestamp >= start,
            EventRow.timestamp <= end,
            EventRow.event_type == EventType.ZONE_ENTER.value,
            EventRow.is_staff == 0,
            EventRow.zone_id.isnot(None),
        )
        .group_by(EventRow.zone_id)
    ).all()
    visited_zones = {zone_id for zone_id, _ in zone_enter_rows if zone_id}
    layout_zones = [z for z in _load_layout_zone_ids() if z not in {"ENTRY_THRESHOLD", "BACKROOM"}]

    anomalies: list[AnomalyItem] = []

    if queue_join_count >= 12:
        anomalies.append(
            AnomalyItem(
                anomaly_type="QUEUE_SPIKE",
                severity="high",
                description=f"Detected {queue_join_count} billing queue joins during the day.",
            )
        )
    elif queue_join_count >= 6:
        anomalies.append(
            AnomalyItem(
                anomaly_type="QUEUE_SPIKE",
                severity="medium",
                description=f"Detected {queue_join_count} billing queue joins during the day.",
            )
        )

    if entry_count >= 10 and conversion_rate < 0.10:
        anomalies.append(
            AnomalyItem(
                anomaly_type="CONVERSION_DROP",
                severity="high",
                description=(
                    f"Conversion rate is {conversion_rate:.2%} for {entry_count} visitors; "
                    "this is below the expected threshold."
                ),
            )
        )

    dead_zones = [zone_id for zone_id in layout_zones if zone_id not in visited_zones]
    for zone_id in dead_zones:
        anomalies.append(
            AnomalyItem(
                anomaly_type="DEAD_ZONE",
                severity="medium",
                zone_id=zone_id,
                description=f"No non-staff visitors entered zone {zone_id} on this day.",
            )
        )

    return AnomalyResponse(
        store_id=store_id,
        date=target.isoformat(),
        anomalies=anomalies,
    )
