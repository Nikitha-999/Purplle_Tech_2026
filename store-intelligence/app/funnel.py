"""Session-based conversion funnel for GET /stores/{id}/funnel."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionRow
from app.models import FunnelResponse, FunnelStage


def _day_bounds(metric_date: date) -> tuple[str, str]:
    start = datetime(metric_date.year, metric_date.month, metric_date.day, tzinfo=timezone.utc)
    end = datetime(metric_date.year, metric_date.month, metric_date.day, 23, 59, 59, tzinfo=timezone.utc)
    return (
        start.isoformat().replace("+00:00", "Z"),
        end.isoformat().replace("+00:00", "Z"),
    )


def _session_in_window(session: SessionRow, start: str, end: str) -> bool:
    if not session.started_at:
        return False
    return start <= session.started_at <= end


def _zones_visited(session: SessionRow) -> list[str]:
    try:
        data = json.loads(session.zones_visited or "[]")
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def compute_funnel(db: Session, store_id: str, metric_date: date | None = None) -> FunnelResponse:
    target = metric_date or date.today()
    start, end = _day_bounds(target)

    sessions = db.scalars(select(SessionRow).where(SessionRow.store_id == store_id)).all()
    customer_sessions = [
        s for s in sessions if s.is_staff == 0 and _session_in_window(s, start, end)
    ]

    entry_count = len(customer_sessions)
    zone_visit_count = sum(1 for s in customer_sessions if len(_zones_visited(s)) > 0)
    queue_count = sum(1 for s in customer_sessions if s.reached_queue == 1)
    purchase_count = sum(1 for s in customer_sessions if s.converted == 1)

    counts = [entry_count, zone_visit_count, queue_count, purchase_count]
    names = ["entry", "zone_visit", "billing_queue", "purchase"]
    labels = ["Entry", "Zone Visit", "Billing Queue", "Purchase"]

    stages: list[FunnelStage] = []
    for idx, (name, label, count) in enumerate(zip(names, labels, counts)):
        previous = counts[idx - 1] if idx > 0 else count
        if idx == 0:
            drop_off = 0.0
        elif previous == 0:
            drop_off = 0.0
        else:
            drop_off = round(100.0 * (previous - count) / previous, 2)
        stages.append(FunnelStage(name=name, label=label, count=count, drop_off_pct=drop_off))

    return FunnelResponse(
        store_id=store_id,
        date=target.isoformat(),
        unit="session",
        stages=stages,
    )
