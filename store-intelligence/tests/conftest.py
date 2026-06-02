import json
import os
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("DATABASE_URL", "sqlite:///./var/test_store_intelligence.db")
os.environ.setdefault("STORE_LAYOUT_PATH", str(ROOT / "data" / "layouts" / "store_layout.json"))
os.environ.setdefault("POS_CSV_PATH", str(ROOT / "data" / "transactions" / "brigade_pos.csv"))

METRIC_DATE = date(2026, 4, 10)


@pytest.fixture(autouse=True)
def reset_database():
    from app.config import get_settings
    import app.database as database
    from app.database import Base, db_session, get_engine, init_db, seed_store_from_layout
    from app.pos_loader import load_pos_transactions

    get_settings.cache_clear()
    database._engine = None
    database._SessionLocal = None

    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    init_db()
    with db_session() as session:
        seed_store_from_layout(session)
        load_pos_transactions(session)

    yield

    Base.metadata.drop_all(bind=engine)
    database._engine = None
    database._SessionLocal = None


@pytest.fixture
def client():
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def metric_date_str():
    return METRIC_DATE.isoformat()


def make_event(
    *,
    event_type: str,
    visitor_id: str,
    event_id: str | None = None,
    store_id: str = "ST1008",
    camera_id: str = "CAM_ENTRY",
    zone_id: str | None = None,
    is_staff: bool = False,
    timestamp: str = "2026-04-10T14:00:00Z",
    session_seq: int = 1,
    queue_depth: int | None = None,
    dwell_ms: int = 0,
) -> dict:
    metadata: dict = {"session_seq": session_seq, "source": "test"}
    if queue_depth is not None:
        metadata["queue_depth"] = queue_depth
    if zone_id:
        metadata["sku_zone"] = zone_id
    return {
        "event_id": event_id or str(uuid4()),
        "store_id": store_id,
        "camera_id": camera_id,
        "visitor_id": visitor_id,
        "event_type": event_type,
        "timestamp": timestamp,
        "zone_id": zone_id,
        "dwell_ms": dwell_ms,
        "is_staff": is_staff,
        "confidence": 0.9,
        "metadata": metadata,
    }


@pytest.fixture
def ingest(client):
    def _ingest(events: list[dict]):
        response = client.post("/events/ingest", json={"events": events})
        assert response.status_code == 200, response.text
        return response.json()

    return _ingest
