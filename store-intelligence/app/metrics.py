"""Store metrics aggregation for GET /stores/{id}/metrics."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import EventRow, SessionRow, TransactionRow
from app.models import EventType, MetricsResponse


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


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


def compute_metrics(db: Session, store_id: str, metric_date: date | None = None) -> MetricsResponse:
    target = metric_date or date.today()
    start, end = _day_bounds(target)

    sessions = db.scalars(select(SessionRow).where(SessionRow.store_id == store_id)).all()
    customer_sessions = [
        s for s in sessions if s.is_staff == 0 and _session_in_window(s, start, end)
    ]

    unique_visitors = len(customer_sessions)
    converted_visitors = sum(1 for s in customer_sessions if s.converted == 1)
    conversion_rate = (converted_visitors / unique_visitors) if unique_visitors > 0 else 0.0

    dwell_rows = db.execute(
        select(EventRow.zone_id, func.avg(EventRow.dwell_ms))
        .where(
            EventRow.store_id == store_id,
            EventRow.is_staff == 0,
            EventRow.timestamp >= start,
            EventRow.timestamp <= end,
            EventRow.event_type.in_([EventType.ZONE_EXIT.value, EventType.ZONE_DWELL.value]),
            EventRow.zone_id.isnot(None),
        )
        .group_by(EventRow.zone_id)
    ).all()
    avg_dwell_by_zone = {
        zone: round(float(avg_ms) / 1000.0, 2) if avg_ms else 0.0 for zone, avg_ms in dwell_rows if zone
    }

    reached_queue = sum(1 for s in customer_sessions if s.reached_queue == 1)
    abandoned = sum(1 for s in customer_sessions if s.abandoned_queue == 1)
    queue_abandonment_rate = (abandoned / reached_queue) if reached_queue > 0 else 0.0

    total_transactions = db.scalar(
        select(func.count())
        .select_from(TransactionRow)
        .where(
            TransactionRow.store_id == store_id,
            TransactionRow.timestamp >= start,
            TransactionRow.timestamp <= end,
        )
    ) or 0

    latest_queue = db.scalar(
        select(EventRow.metadata_json)
        .where(
            EventRow.store_id == store_id,
            EventRow.event_type == EventType.BILLING_QUEUE_JOIN.value,
            EventRow.timestamp >= start,
            EventRow.timestamp <= end,
        )
        .order_by(EventRow.timestamp.desc())
        .limit(1)
    )
    current_queue_depth = 0
    if latest_queue:
        import json

        try:
            meta = json.loads(latest_queue)
            current_queue_depth = int(meta.get("queue_depth") or 0)
        except (json.JSONDecodeError, TypeError, ValueError):
            current_queue_depth = 0

    return MetricsResponse(
        store_id=store_id,
        date=target.isoformat(),
        unique_visitors=unique_visitors,
        converted_visitors=converted_visitors,
        conversion_rate=round(conversion_rate, 4),
        avg_dwell_by_zone=avg_dwell_by_zone,
        current_queue_depth=current_queue_depth,
        queue_abandonment_rate=round(queue_abandonment_rate, 4),
        total_transactions=int(total_transactions),
        data_as_of=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
