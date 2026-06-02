from app.models import EventType


def test_anomalies_dead_zone_when_no_events(client):
    response = client.get("/stores/ST1008/anomalies?date=2026-04-10")
    assert response.status_code == 200
    body = response.json()
    assert body["store_id"] == "ST1008"
    assert any(item["anomaly_type"] == "DEAD_ZONE" for item in body["anomalies"])


def test_anomalies_queue_spike_detected(client, ingest):
    events = []
    for idx in range(12):
        events.append(
            {
                "event_id": f"spike-{idx}",
                "store_id": "ST1008",
                "camera_id": "CAM_BILLING",
                "visitor_id": f"V{idx}",
                "event_type": EventType.BILLING_QUEUE_JOIN.value,
                "timestamp": "2026-04-10T14:00:00Z",
                "zone_id": "BILLING_QUEUE",
                "dwell_ms": 0,
                "is_staff": False,
                "confidence": 0.8,
                "metadata": {"session_seq": idx + 1, "source": "test", "queue_depth": 1},
            }
        )
    ingest(events)
    response = client.get("/stores/ST1008/anomalies?date=2026-04-10")
    assert response.status_code == 200
    body = response.json()
    assert any(item["anomaly_type"] == "QUEUE_SPIKE" for item in body["anomalies"])
