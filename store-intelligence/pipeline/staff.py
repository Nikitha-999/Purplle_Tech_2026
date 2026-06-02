"""
Lightweight staff classifier (heuristic).

Assumptions (documented for reviewers):
- CAM_BACKROOM is staff-only space; any person detected there is staff.
- Staff often remain on camera for most of a clip (restocking, counter duty).
- Staff traverse many zones repeatedly vs a typical shopper path.

Rules:
  is_staff = seen on CAM_BACKROOM
          OR visible > 75% of sampled frames
          OR zone_transition_count >= 8
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TrackStats:
    track_id: int
    frames_visible: int = 0
    zone_transitions: int = 0
    seen_on_backroom: bool = False
    is_staff: bool = False


@dataclass
class StaffClassifier:
    camera_id: str
    total_sampled_frames: int = 0
    tracks: dict[int, TrackStats] = field(default_factory=dict)

    def register_frame(self) -> None:
        self.total_sampled_frames += 1

    def observe(
        self,
        track_id: int,
        *,
        zone_transition_delta: int = 0,
        on_backroom_camera: bool = False,
    ) -> None:
        stats = self.tracks.setdefault(track_id, TrackStats(track_id=track_id))
        stats.frames_visible += 1
        stats.zone_transitions += zone_transition_delta
        if on_backroom_camera:
            stats.seen_on_backroom = True

    def finalize(self) -> set[int]:
        """Return track IDs classified as staff."""
        staff_ids: set[int] = set()
        total = max(self.total_sampled_frames, 1)
        for track_id, stats in self.tracks.items():
            presence_ratio = stats.frames_visible / total
            if stats.seen_on_backroom:
                stats.is_staff = True
            elif presence_ratio > 0.75:
                stats.is_staff = True
            elif stats.zone_transitions >= 8:
                stats.is_staff = True
            if stats.is_staff:
                staff_ids.add(track_id)
        return staff_ids

    def is_staff_track(self, track_id: int) -> bool:
        stats = self.tracks.get(track_id)
        return bool(stats and stats.is_staff)
