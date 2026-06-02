from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import EventRow
from app.models import EventType, HeatmapResponse, HeatmapZone


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


def _score_zone(visit_count: int, avg_dwell_sec: float) -> int:
    if visit_count <= 0:
        return 0
    visit_score = min(60, int(min(visit_count, 20) * 3))
    dwell_score = min(40, int(min(avg_dwell_sec, 120.0) / 3.0))
    return min(100, visit_score + dwell_score)


def compute_heatmap(db: Session, store_id: str, metric_date: date | None = None) -> HeatmapResponse:
    target = metric_date or date.today()
    start, end = _day_bounds(target)

    zone_ids = _load_layout_zone_ids()
    if not zone_ids:
        zone_ids = []

    visit_rows = db.execute(
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
    dwell_rows = db.execute(
        select(EventRow.zone_id, func.avg(EventRow.dwell_ms))
        .where(
            EventRow.store_id == store_id,
            EventRow.timestamp >= start,
            EventRow.timestamp <= end,
            EventRow.event_type.in_([EventType.ZONE_EXIT.value, EventType.ZONE_DWELL.value]),
            EventRow.is_staff == 0,
            EventRow.zone_id.isnot(None),
        )
        .group_by(EventRow.zone_id)
    ).all()

    visits: dict[str, int] = {zone_id: int(count) for zone_id, count in visit_rows if zone_id}
    dwell: dict[str, float] = {zone_id: float(avg_ms or 0.0) / 1000.0 for zone_id, avg_ms in dwell_rows if zone_id}

    all_zone_ids = sorted({*zone_ids, *visits.keys(), *dwell.keys()})
    zones: list[HeatmapZone] = []
    total_visits = 0

    for zone_id in all_zone_ids:
        count = visits.get(zone_id, 0)
        avg_sec = round(dwell.get(zone_id, 0.0), 2)
        zones.append(
            HeatmapZone(
                zone_id=zone_id,
                visit_count=count,
                avg_dwell_sec=avg_sec,
                score_0_100=_score_zone(count, avg_sec),
            )
        )
        total_visits += count

    if total_visits >= 30:
        confidence = "high"
    elif total_visits >= 8:
        confidence = "medium"
    else:
        confidence = "low"

    return HeatmapResponse(
        store_id=store_id,
        date=target.isoformat(),
        zones=zones,
        data_confidence=confidence,
    )
