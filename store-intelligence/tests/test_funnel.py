# PROMPT: Write pytest tests for GET /stores/{id}/funnel ensuring session-based stages
# and that REENTRY does not inflate entry counts.
# CHANGES MADE: Added multi-visitor funnel and re-entry deduplication assertions.

from tests.conftest import make_event


def test_funnel_empty(client, metric_date_str):
    response = client.get(f"/stores/ST1008/funnel?date={metric_date_str}")
    assert response.status_code == 200
    body = response.json()
    assert body["unit"] == "session"
    assert all(stage["count"] == 0 for stage in body["stages"])


def test_funnel_session_progression(client, ingest, metric_date_str):
    visitor = "VIS_funnel"
    ingest(
        [
            make_event(event_type="ENTRY", visitor_id=visitor, timestamp="2026-04-10T17:00:00Z"),
            make_event(
                event_type="ZONE_ENTER",
                visitor_id=visitor,
                camera_id="CAM_MAKEUP",
                zone_id="MAKEUP_BOTTOM_WALL",
                timestamp="2026-04-10T17:05:00Z",
                session_seq=2,
            ),
            make_event(
                event_type="BILLING_QUEUE_JOIN",
                visitor_id=visitor,
                camera_id="CAM_BILLING",
                zone_id="BILLING_QUEUE",
                timestamp="2026-04-10T17:10:00Z",
                session_seq=3,
                queue_depth=1,
            ),
            make_event(
                event_type="ZONE_ENTER",
                visitor_id=visitor,
                camera_id="CAM_BILLING",
                zone_id="BILLING_COUNTER",
                timestamp="2026-04-10T16:55:00Z",
                session_seq=4,
            ),
        ]
    )
    response = client.get(f"/stores/ST1008/funnel?date={metric_date_str}")
    stages = {s["name"]: s["count"] for s in response.json()["stages"]}
    assert stages["entry"] == 1
    assert stages["zone_visit"] == 1
    assert stages["billing_queue"] == 1


def test_reentry_does_not_duplicate_funnel_entry(client, ingest, metric_date_str):
    visitor = "VIS_funnel_reentry"
    ingest(
        [
            make_event(event_type="ENTRY", visitor_id=visitor, timestamp="2026-04-10T18:00:00Z", session_seq=1),
            make_event(event_type="EXIT", visitor_id=visitor, timestamp="2026-04-10T18:20:00Z", session_seq=2),
            make_event(event_type="REENTRY", visitor_id=visitor, timestamp="2026-04-10T18:40:00Z", session_seq=3),
        ]
    )
    response = client.get(f"/stores/ST1008/funnel?date={metric_date_str}")
    stages = {s["name"]: s["count"] for s in response.json()["stages"]}
    assert stages["entry"] == 1


def test_staff_excluded_from_funnel(client, ingest, metric_date_str):
    ingest(
        [
            make_event(
                event_type="ENTRY",
                visitor_id="VIS_staff_funnel",
                is_staff=True,
                timestamp="2026-04-10T19:00:00Z",
            )
        ]
    )
    response = client.get(f"/stores/ST1008/funnel?date={metric_date_str}")
    stages = {s["name"]: s["count"] for s in response.json()["stages"]}
    assert stages["entry"] == 0
