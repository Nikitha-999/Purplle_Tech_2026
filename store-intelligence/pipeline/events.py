"""Build and write challenge-compliant events."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from app.models import Event, EventMetadata, EventType


def parse_anchor(anchor: str) -> datetime:
    normalized = anchor.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def frame_to_timestamp(anchor: datetime, frame_idx: int, fps: float) -> datetime:
    seconds = frame_idx / max(fps, 1.0)
    ts = anchor + timedelta(seconds=seconds)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def format_utc(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def visitor_id_for_track(store_id: str, camera_id: str, track_id: int) -> str:
    short = camera_id.replace("CAM_", "")
    return f"VIS_{store_id}_{short}_{track_id}"


class EventCollector:
    def __init__(self, store_id: str) -> None:
        self.store_id = store_id
        self.events: list[dict] = []
        self._session_seq: dict[str, int] = {}

    def _next_seq(self, visitor_id: str) -> int:
        current = self._session_seq.get(visitor_id, 0) + 1
        self._session_seq[visitor_id] = current
        return current

    def emit(
        self,
        *,
        camera_id: str,
        visitor_id: str,
        event_type: EventType | str,
        timestamp: datetime,
        zone_id: str | None = None,
        dwell_ms: int = 0,
        is_staff: bool = False,
        confidence: float = 0.85,
        track_id: int | None = None,
        queue_depth: int | None = None,
        sku_zone: str | None = None,
    ) -> dict:
        etype = event_type if isinstance(event_type, EventType) else EventType(event_type)
        meta = EventMetadata(
            session_seq=self._next_seq(visitor_id),
            track_id=track_id,
            queue_depth=queue_depth,
            sku_zone=sku_zone,
            source="pipeline_v1",
        )
        event = Event(
            event_id=str(uuid4()),
            store_id=self.store_id,
            camera_id=camera_id,
            visitor_id=visitor_id,
            event_type=etype,
            timestamp=timestamp,
            zone_id=zone_id,
            dwell_ms=dwell_ms,
            is_staff=is_staff,
            confidence=confidence,
            metadata=meta,
        )
        payload = event.model_dump(mode="json")
        payload["timestamp"] = format_utc(timestamp)
        self.events.append(payload)
        return payload

    def apply_staff_flags(self, staff_keys: set[tuple[str, int]]) -> None:
        """Patch is_staff on events for (camera_id, track_id) pairs."""
        for event in self.events:
            meta = event.get("metadata") or {}
            track_id = meta.get("track_id")
            key = (event["camera_id"], track_id)
            if key in staff_keys:
                event["is_staff"] = True

    def write_jsonl(self, path: str | Path) -> int:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as handle:
            for event in self.events:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        return len(self.events)

    def counts_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in self.events:
            et = event["event_type"]
            counts[et] = counts.get(et, 0) + 1
        return counts
