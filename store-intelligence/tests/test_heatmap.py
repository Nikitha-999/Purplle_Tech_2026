from app.models import EventType


def test_heatmap_zone_metrics(client, ingest):
    events = [
        {
            "event_id": "hm-1",
            "store_id": "ST1008",
            "camera_id": "CAM_SKINCARE",
            "visitor_id": "V1",
            "event_type": EventType.ZONE_ENTER.value,
            "timestamp": "2026-04-10T14:05:00Z",
            "zone_id": "SKIN_TOP_WALL",
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.85,
            "metadata": {"session_seq": 1, "source": "test"},
        },
        {
            "event_id": "hm-2",
            "store_id": "ST1008",
            "camera_id": "CAM_SKINCARE",
            "visitor_id": "V1",
            "event_type": EventType.ZONE_EXIT.value,
            "timestamp": "2026-04-10T14:06:00Z",
            "zone_id": "SKIN_TOP_WALL",
            "dwell_ms": 60000,
            "is_staff": False,
            "confidence": 0.85,
            "metadata": {"session_seq": 2, "source": "test"},
        },
    ]
    ingest(events)

    response = client.get("/stores/ST1008/heatmap?date=2026-04-10")
    assert response.status_code == 200
    body = response.json()
    assert body["store_id"] == "ST1008"
    skin_zone = next((zone for zone in body["zones"] if zone["zone_id"] == "SKIN_TOP_WALL"), None)
    assert skin_zone is not None
    assert skin_zone["visit_count"] == 1
    assert skin_zone["avg_dwell_sec"] == 60.0
    assert skin_zone["score_0_100"] > 0
    assert body["data_confidence"] in {"low", "medium", "high"}
