# PROMPT: Write pytest tests for POST /events/ingest covering idempotency,
# empty batches, partial validation failures, and session lifecycle side effects.
# CHANGES MADE: Added re-entry test; uses shared conftest factories.

from uuid import uuid4

from sqlalchemy import select

from app.database import SessionRow
from tests.conftest import make_event


def test_empty_ingestion(client):
    response = client.post("/events/ingest", json={"events": []})
    assert response.status_code == 200
    body = response.json()
    assert body == {"accepted": 0, "duplicates": 0, "rejected": 0, "errors": []}


def test_duplicate_ingestion(client, ingest):
    event = make_event(event_type="ENTRY", visitor_id="VIS_dup_test")
    first = ingest([event])
    assert first["accepted"] == 1
    second = ingest([event])
    assert second["accepted"] == 0
    assert second["duplicates"] == 1


def test_partial_validation_failure(client):
    good = make_event(event_type="ENTRY", visitor_id="VIS_partial_ok")
    bad = {"event_id": "not-a-uuid", "store_id": "ST1008"}
    response = client.post("/events/ingest", json={"events": [good, bad]})
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] == 1
    assert body["rejected"] == 1
    assert len(body["errors"]) == 1


def test_session_lifecycle(client, ingest):
    visitor = "VIS_lifecycle"
    events = [
        make_event(event_type="ENTRY", visitor_id=visitor, timestamp="2026-04-10T12:00:00Z", session_seq=1),
        make_event(
            event_type="ZONE_ENTER",
            visitor_id=visitor,
            camera_id="CAM_SKINCARE",
            zone_id="SKIN_TOP_WALL",
            timestamp="2026-04-10T12:05:00Z",
            session_seq=2,
        ),
        make_event(event_type="EXIT", visitor_id=visitor, timestamp="2026-04-10T12:30:00Z", session_seq=3),
    ]
    ingest(events)

    from app.database import db_session

    with db_session() as db:
        row = db.get(SessionRow, visitor)
        assert row is not None
        assert row.started_at == "2026-04-10T12:00:00Z"
        assert row.ended_at == "2026-04-10T12:30:00Z"
        zones = __import__("json").loads(row.zones_visited)
        assert "SKIN_TOP_WALL" in zones


def test_reentry_reopens_session(client, ingest):
    visitor = "VIS_reentry"
    events = [
        make_event(event_type="ENTRY", visitor_id=visitor, timestamp="2026-04-10T15:00:00Z", session_seq=1),
        make_event(event_type="EXIT", visitor_id=visitor, timestamp="2026-04-10T15:20:00Z", session_seq=2),
        make_event(event_type="REENTRY", visitor_id=visitor, timestamp="2026-04-10T15:40:00Z", session_seq=3),
    ]
    ingest(events)

    from app.database import db_session

    with db_session() as db:
        row = db.get(SessionRow, visitor)
        assert row.reentry_count == 1
        assert row.ended_at is None


def test_queue_flags(client, ingest):
    visitor = "VIS_queue"
    events = [
        make_event(event_type="ENTRY", visitor_id=visitor, timestamp="2026-04-10T18:00:00Z"),
        make_event(
            event_type="BILLING_QUEUE_JOIN",
            visitor_id=visitor,
            camera_id="CAM_BILLING",
            zone_id="BILLING_QUEUE",
            timestamp="2026-04-10T18:10:00Z",
            session_seq=2,
            queue_depth=2,
        ),
        make_event(
            event_type="BILLING_QUEUE_ABANDON",
            visitor_id=visitor,
            camera_id="CAM_BILLING",
            zone_id="BILLING_QUEUE",
            timestamp="2026-04-10T18:15:00Z",
            session_seq=3,
            queue_depth=1,
        ),
    ]
    ingest(events)

    from app.database import db_session

    with db_session() as db:
        row = db.get(SessionRow, visitor)
        assert row.reached_queue == 1
        assert row.abandoned_queue == 1
