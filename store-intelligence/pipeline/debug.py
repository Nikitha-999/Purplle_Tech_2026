"""Debug frame overlays — bounding boxes, track IDs, zone polygons."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from pipeline.tracker import Track
from pipeline.zones import CameraZones, point_in_polygon


ZONE_COLORS = {
    "ENTRY_THRESHOLD": (0, 165, 255),
    "FOH_AISLE": (200, 200, 0),
    "SKIN_TOP_WALL": (0, 255, 0),
    "MAKEUP_BOTTOM_WALL": (255, 128, 0),
    "MAKEUP_STATION": (255, 0, 255),
    "BILLING_QUEUE": (0, 255, 255),
    "BILLING_COUNTER": (255, 255, 0),
    "BACKROOM": (128, 128, 255),
}


def draw_zones(frame: np.ndarray, camera_zones: CameraZones, alpha: float = 0.25) -> np.ndarray:
    overlay = frame.copy()
    for zone in camera_zones.zones:
        color = ZONE_COLORS.get(zone.zone_id, (180, 180, 180))
        pts = np.array(zone.polygon, dtype=np.int32)
        cv2.fillPoly(overlay, [pts], color)
        cv2.polylines(overlay, [pts], True, color, 2)
        cx = int(sum(p[0] for p in zone.polygon) / len(zone.polygon))
        cy = int(sum(p[1] for p in zone.polygon) / len(zone.polygon))
        cv2.putText(
            overlay,
            zone.zone_id,
            (cx - 40, cy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
    if camera_zones.entry_line:
        p1 = tuple(map(int, camera_zones.entry_line["p1"]))
        p2 = tuple(map(int, camera_zones.entry_line["p2"]))
        cv2.line(overlay, p1, p2, (0, 0, 255), 3)
        cv2.putText(overlay, "ENTRY_LINE", p1, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)


def draw_tracks(frame: np.ndarray, tracks: list[Track], staff_ids: set[int] | None = None) -> np.ndarray:
    staff_ids = staff_ids or set()
    for track in tracks:
        x1, y1, x2, y2 = map(int, track.bbox)
        color = (0, 0, 255) if track.track_id in staff_ids else (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"ID {track.track_id} {track.confidence:.2f}"
        if track.track_id in staff_ids:
            label += " STAFF"
        cv2.putText(
            frame,
            label,
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA,
        )
        cx, cy = map(int, track.centroid)
        cv2.circle(frame, (cx, cy), 4, color, -1)
    return frame


def save_debug_frame(
    frame: np.ndarray,
    camera_id: str,
    frame_idx: int,
    tracks: list[Track],
    camera_zones: CameraZones,
    output_dir: str | Path,
    staff_ids: set[int] | None = None,
) -> None:
    out_dir = Path(output_dir) / camera_id
    out_dir.mkdir(parents=True, exist_ok=True)
    canvas = draw_zones(frame, camera_zones)
    canvas = draw_tracks(canvas, tracks, staff_ids)
    path = out_dir / f"frame_{frame_idx:06d}.jpg"
    cv2.imwrite(str(path), canvas)
