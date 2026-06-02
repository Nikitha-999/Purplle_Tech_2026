"""ByteTrack multi-object tracking via supervision."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from pipeline.detect import Detection, detections_to_supervision


@dataclass
class Track:
    track_id: int
    bbox: list[float]
    confidence: float
    centroid: tuple[float, float]
    history: list[tuple[float, float]] = field(default_factory=list)

    def update(self, bbox: list[float], confidence: float, max_history: int = 60) -> None:
        self.bbox = bbox
        self.confidence = confidence
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
        self.centroid = (cx, cy)
        self.history.append(self.centroid)
        if len(self.history) > max_history:
            self.history = self.history[-max_history:]


class ByteTracker:
    """Stable per-video track IDs using ByteTrack."""

    def __init__(self, frame_rate: int = 30) -> None:
        import supervision as sv

        self._tracker = sv.ByteTrack(
            track_activation_threshold=0.35,
            lost_track_buffer=30,
            minimum_matching_threshold=0.8,
            frame_rate=frame_rate,
        )
        self._tracks: dict[int, Track] = {}

    def update(self, detections: list[Detection]) -> list[Track]:
        sv_det = detections_to_supervision(detections)
        tracked = self._tracker.update_with_detections(sv_det)
        tracks: list[Track] = []
        if tracked.tracker_id is None:
            return tracks
        for idx, track_id in enumerate(tracked.tracker_id):
            if track_id is None:
                continue
            bbox = tracked.xyxy[idx].tolist()
            conf = float(tracked.confidence[idx]) if tracked.confidence is not None else 0.5
            track_id_int = int(track_id)
            existing = self._tracks.get(track_id_int)
            if existing is not None:
                existing.update([float(v) for v in bbox], conf)
                track = existing
            else:
                centroid = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
                track = Track(
                    track_id=track_id_int,
                    bbox=[float(v) for v in bbox],
                    confidence=conf,
                    centroid=centroid,
                    history=[centroid],
                )
                self._tracks[track_id_int] = track
            tracks.append(track)
        return tracks


def is_tracking_available() -> bool:
    try:
        import supervision  # noqa: F401

        return True
    except ImportError:
        return False
