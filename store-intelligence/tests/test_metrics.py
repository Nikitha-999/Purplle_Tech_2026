# PROMPT: Write pytest tests for GET /stores/{id}/metrics including zero visitors,
# staff exclusion, and conversion after billing + POS alignment.
# CHANGES MADE: Uses date=2026-04-10 to match POS CSV; conversion window test.

from tests.conftest import make_event


def test_zero_visitors_metrics(client, metric_date_str):
    response = client.get(f"/stores/ST1008/metrics?date={metric_date_str}")
    assert response.status_code == 200
    body = response.json()
    assert body["unique_visitors"] == 0
    assert body["converted_visitors"] == 0
    assert body["conversion_rate"] == 0.0
    assert body["total_transactions"] >= 0


def test_staff_exclusion_metrics(client, ingest, metric_date_str):
    ingest(
        [
            make_event(
                event_type="ENTRY",
                visitor_id="VIS_staff_only",
                is_staff=True,
                timestamp="2026-04-10T16:00:00Z",
            )
        ]
    )
    response = client.get(f"/stores/ST1008/metrics?date={metric_date_str}")
    body = response.json()
    assert body["unique_visitors"] == 0


def test_metrics_with_visitor_and_dwell(client, ingest, metric_date_str):
    visitor = "VIS_metrics"
    ingest(
        [
            make_event(event_type="ENTRY", visitor_id=visitor, timestamp="2026-04-10T16:45:00Z"),
            make_event(
                event_type="ZONE_DWELL",
                visitor_id=visitor,
                camera_id="CAM_SKINCARE",
                zone_id="SKIN_TOP_WALL",
                timestamp="2026-04-10T16:50:00Z",
                dwell_ms=30000,
                session_seq=2,
            ),
        ]
    )
    response = client.get(f"/stores/ST1008/metrics?date={metric_date_str}")
    body = response.json()
    assert body["unique_visitors"] == 1
    assert "SKIN_TOP_WALL" in body["avg_dwell_by_zone"]


def test_pos_transactions_loaded(client, metric_date_str):
    response = client.get(f"/stores/ST1008/metrics?date={metric_date_str}")
    body = response.json()
    assert body["total_transactions"] == 24


def test_store_alias_metrics(client, metric_date_str):
    response = client.get(f"/stores/STORE_BLR_002/metrics?date={metric_date_str}")
    assert response.status_code == 200
    assert response.json()["store_id"] == "ST1008"


def test_conversion_correlation(client, ingest, metric_date_str):
    visitor = "VIS_convert"
    ingest(
        [
            make_event(event_type="ENTRY", visitor_id=visitor, timestamp="2026-04-10T16:50:00Z"),
            make_event(
                event_type="ZONE_ENTER",
                visitor_id=visitor,
                camera_id="CAM_BILLING",
                zone_id="BILLING_COUNTER",
                timestamp="2026-04-10T16:55:00Z",
                session_seq=2,
            ),
        ]
    )
    response = client.get(f"/stores/ST1008/metrics?date={metric_date_str}")
    body = response.json()
    assert body["unique_visitors"] == 1
    assert body["converted_visitors"] == 1
    assert body["conversion_rate"] == 1.0
