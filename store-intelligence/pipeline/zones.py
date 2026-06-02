"""Zone polygons, line crossing, and queue depth helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def load_store_layout(layout_path: str | Path) -> dict[str, Any]:
    path = Path(layout_path)
    return json.loads(path.read_text(encoding="utf-8"))


def get_camera_config(layout: dict[str, Any], camera_id: str) -> dict[str, Any] | None:
    for camera in layout.get("cameras", []):
        if camera.get("camera_id") == camera_id:
            return camera
    return None


def point_in_polygon(point: tuple[float, float], polygon: list[list[float]]) -> bool:
    """Ray-casting point-in-polygon test."""
    x, y = point
    inside = False
    n = len(polygon)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def _cross(ax: float, ay: float, bx: float, by: float) -> float:
    return ax * by - ay * bx


def line_side(
    p1: tuple[float, float],
    p2: tuple[float, float],
    point: tuple[float, float],
) -> float:
    """Signed cross product — positive/negative indicates side of directed line p1→p2."""
    return _cross(
        p2[0] - p1[0],
        p2[1] - p1[1],
        point[0] - p1[0],
        point[1] - p1[1],
    )


def line_crossing(
    prev_side: float | None,
    curr_side: float,
    *,
    inbound_positive: bool = True,
) -> str | None:
    """
    Detect threshold crossing between frames.
    Returns 'ENTRY' for inbound cross, 'EXIT' for outbound, else None.
    """
    if prev_side is None or prev_side == 0 or curr_side == 0:
        return None
    if prev_side < 0 < curr_side:
        return "ENTRY" if inbound_positive else "EXIT"
    if prev_side > 0 > curr_side:
        return "EXIT" if inbound_positive else "ENTRY"
    return None


@dataclass
class ZoneDefinition:
    zone_id: str
    sku_zone: str
    polygon: list[list[float]]


@dataclass
class CameraZones:
    camera_id: str
    zones: list[ZoneDefinition]
    entry_line: dict[str, Any] | None = None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> CameraZones:
        zones = [
            ZoneDefinition(
                zone_id=z["zone_id"],
                sku_zone=z.get("sku_zone", z["zone_id"]),
                polygon=z["polygon"],
            )
            for z in config.get("zones", [])
        ]
        return cls(
            camera_id=config["camera_id"],
            zones=zones,
            entry_line=config.get("entry_line"),
        )

    def zone_at_point(self, point: tuple[float, float]) -> list[str]:
        hits = []
        for zone in self.zones:
            if point_in_polygon(point, zone.polygon):
                hits.append(zone.zone_id)
        return hits

    def sku_for_zone(self, zone_id: str) -> str:
        for zone in self.zones:
            if zone.zone_id == zone_id:
                return zone.sku_zone
        return zone_id


def zone_enter(current: set[str], detected: set[str]) -> set[str]:
    return detected - current


def zone_exit(current: set[str], detected: set[str]) -> set[str]:
    return current - detected


def queue_depth(
    tracks: list[tuple[tuple[float, float], bool]],
    queue_polygon: list[list[float]],
) -> int:
    """Count non-staff centroids inside the billing queue polygon."""
    depth = 0
    for centroid, is_staff in tracks:
        if is_staff:
            continue
        if point_in_polygon(centroid, queue_polygon):
            depth += 1
    return depth


@dataclass
class TrackZoneState:
    inside_zones: set[str] = field(default_factory=set)
    pending_enter: dict[str, int] = field(default_factory=dict)
    pending_exit: dict[str, int] = field(default_factory=dict)
    last_dwell_at: dict[str, float] = field(default_factory=dict)
    zone_entered_at: dict[str, float] = field(default_factory=dict)
    line_side_value: float | None = None
    has_open_visit: bool = False
    exited_once: bool = False
    queue_joined: bool = False
    reached_counter: bool = False
    zone_transition_count: int = 0

    DEBOUNCE_FRAMES = 3
    DWELL_INTERVAL_SEC = 30.0
