from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import EventRow, StoreRow, check_database_connection
from app.models import HealthResponse, StoreHealth


def _parse_iso_utc(value: str) -> datetime:
  normalized = value.replace("Z", "+00:00")
  return datetime.fromisoformat(normalized).astimezone(timezone.utc)


def _minutes_between(later: datetime, earlier: datetime) -> float:
  return max(0.0, (later - earlier).total_seconds() / 60.0)


def build_health_response(session: Session) -> HealthResponse:
  settings = get_settings()
  now = datetime.now(timezone.utc)
  warnings: list[str] = []

  if not check_database_connection():
    return HealthResponse(
      status="degraded",
      database="down",
      version="0.1.0",
      stores=[],
      warnings=["database_unavailable"],
    )

  store_rows = session.scalars(select(StoreRow)).all()
  if not store_rows:
    warnings.append("no_stores_configured")

  store_health: list[StoreHealth] = []
  global_stale = False

  for store in store_rows:
    store_warnings: list[str] = []
    last_ts = session.scalar(
      select(func.max(EventRow.timestamp)).where(EventRow.store_id == store.store_id)
    )
    lag_minutes: float | None = None
    if last_ts:
      last_dt = _parse_iso_utc(last_ts)
      lag_minutes = round(_minutes_between(now, last_dt), 2)
      if lag_minutes > settings.stale_feed_minutes:
        store_warnings.append("STALE_FEED")
        global_stale = True
    else:
      store_warnings.append("NO_EVENTS_INGESTED")

    store_health.append(
      StoreHealth(
        store_id=store.store_id,
        last_event_at=last_ts,
        lag_minutes=lag_minutes,
        warnings=store_warnings,
      )
    )

  status = "degraded" if global_stale or warnings else "ok"
  return HealthResponse(
    status=status,
    database="up",
    version="0.1.0",
    stores=store_health,
    warnings=warnings,
  )
