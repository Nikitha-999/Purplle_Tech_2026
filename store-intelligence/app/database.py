from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import Column, Float, Integer, String, Text, create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
  pass


class StoreRow(Base):
  __tablename__ = "stores"

  store_id = Column(String(64), primary_key=True)
  store_name = Column(String(255), nullable=False)
  timezone = Column(String(64), nullable=False, default="Asia/Kolkata")
  created_at = Column(String(64), nullable=False)


class EventRow(Base):
  __tablename__ = "events"

  event_id = Column(String(64), primary_key=True)
  store_id = Column(String(64), nullable=False, index=True)
  camera_id = Column(String(64), nullable=False)
  visitor_id = Column(String(128), nullable=False, index=True)
  event_type = Column(String(64), nullable=False, index=True)
  timestamp = Column(String(64), nullable=False, index=True)
  zone_id = Column(String(64), nullable=True)
  dwell_ms = Column(Integer, nullable=False, default=0)
  is_staff = Column(Integer, nullable=False, default=0)
  confidence = Column(Float, nullable=False, default=0.0)
  metadata_json = Column(Text, nullable=False, default="{}")
  ingested_at = Column(String(64), nullable=False)


class SessionRow(Base):
  __tablename__ = "sessions"

  session_id = Column(String(128), primary_key=True)
  store_id = Column(String(64), nullable=False, index=True)
  visitor_id = Column(String(128), nullable=False, unique=True, index=True)
  started_at = Column(String(64), nullable=True)
  ended_at = Column(String(64), nullable=True)
  is_staff = Column(Integer, nullable=False, default=0)
  reentry_count = Column(Integer, nullable=False, default=0)
  reached_billing = Column(Integer, nullable=False, default=0)
  reached_queue = Column(Integer, nullable=False, default=0)
  abandoned_queue = Column(Integer, nullable=False, default=0)
  converted = Column(Integer, nullable=False, default=0)
  conversion_txn_id = Column(String(64), nullable=True)
  zones_visited = Column(Text, nullable=False, default="[]")


class TransactionRow(Base):
  __tablename__ = "transactions"

  transaction_id = Column(String(64), primary_key=True)
  store_id = Column(String(64), nullable=False, index=True)
  timestamp = Column(String(64), nullable=False, index=True)
  basket_value_inr = Column(Float, nullable=False, default=0.0)
  salesperson = Column(String(255), nullable=True)
  source = Column(String(64), nullable=False, default="pos_csv")


class MetricSnapshotRow(Base):
  __tablename__ = "metrics"

  id = Column(Integer, primary_key=True, autoincrement=True)
  store_id = Column(String(64), nullable=False, index=True)
  metric_date = Column(String(16), nullable=False, index=True)
  payload_json = Column(Text, nullable=False, default="{}")
  computed_at = Column(String(64), nullable=False)


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _utc_now_iso() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ensure_sqlite_directory(database_url: str) -> None:
  if not database_url.startswith("sqlite:///"):
    return
  raw = database_url.replace("sqlite:///", "", 1)
  path = Path(raw)
  if path.parent and str(path.parent) not in (".", ""):
    path.parent.mkdir(parents=True, exist_ok=True)


@event.listens_for(Engine, "connect")
def _sqlite_pragma(dbapi_connection, connection_record) -> None:
  if dbapi_connection.__class__.__module__.startswith("sqlite3"):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_engine() -> Engine:
  global _engine
  if _engine is None:
    settings = get_settings()
    _ensure_sqlite_directory(settings.database_url)
    _engine = create_engine(
      settings.database_url,
      connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
      pool_pre_ping=True,
    )
  return _engine


def get_session_factory() -> sessionmaker[Session]:
  global _SessionLocal
  if _SessionLocal is None:
    _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False, expire_on_commit=False)
  return _SessionLocal


def get_db() -> Generator[Session, None, None]:
  session = get_session_factory()()
  try:
    yield session
  finally:
    session.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
  session = get_session_factory()()
  try:
    yield session
    session.commit()
  except Exception:
    session.rollback()
    raise
  finally:
    session.close()


def init_db() -> None:
  engine = get_engine()
  Base.metadata.create_all(bind=engine)
  with engine.connect() as conn:
    conn.execute(
      text(
        "CREATE INDEX IF NOT EXISTS ix_events_store_timestamp "
        "ON events (store_id, timestamp)"
      )
    )
    conn.execute(
      text(
        "CREATE INDEX IF NOT EXISTS ix_events_store_visitor_timestamp "
        "ON events (store_id, visitor_id, timestamp)"
      )
    )
    conn.execute(
      text(
        "CREATE INDEX IF NOT EXISTS ix_sessions_store_started "
        "ON sessions (store_id, started_at)"
      )
    )
    conn.commit()


def check_database_connection() -> bool:
  try:
    with get_engine().connect() as conn:
      conn.execute(text("SELECT 1"))
    return True
  except Exception:
    return False


def seed_store_from_layout(session: Session) -> None:
  import json

  settings = get_settings()
  layout_path = settings.layout_path
  if not layout_path.is_file():
    return
  payload = json.loads(layout_path.read_text(encoding="utf-8"))
  store_id = payload["store_id"]
  existing = session.get(StoreRow, store_id)
  if existing:
    return
  session.add(
    StoreRow(
      store_id=store_id,
      store_name=payload.get("store_name", store_id),
      timezone=payload.get("timezone", "Asia/Kolkata"),
      created_at=_utc_now_iso(),
    )
  )
  session.commit()
