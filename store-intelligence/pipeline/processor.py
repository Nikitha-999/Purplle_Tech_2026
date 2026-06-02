"""Process a single CCTV clip and emit structured events."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import cv2

from app.models import EventType
from pipeline.debug import save_debug_frame
from pipeline.detect import detect_persons
from pipeline.events import EventCollector, frame_to_timestamp, parse_anchor, visitor_id_for_track
from pipeline.staff import StaffClassifier
from pipeline.tracker import ByteTracker, Track
from pipeline.zones import (
    CameraZones,
    TrackZoneState,
    line_crossing,
    line_side,
    point_in_polygon,
    queue_depth,
    zone_enter,
    zone_exit,
)

logger = logging.getLogger("store_intelligence.processor")


@dataclass
class VideoSummary:
    camera_id: str
    video_file: str
    frames_processed: int
    tracks_seen: int
    staff_tracks: int
    events_by_type: dict[str, int] = field(default_factory=dict)


def _emit_entry_exit(
    collector: EventCollector,
    *,
    camera_id: str,
    store_id: str,
    track: Track,
    state: TrackZoneState,
    timestamp,
    is_staff: bool,
    kind: str,
) -> None:
    visitor_id = visitor_id_for_track(store_id, camera_id, track.track_id)
    if kind == "ENTRY":
        if state.exited_once and not state.has_open_visit:
            collector.emit(
                camera_id=camera_id,
                visitor_id=visitor_id,
                event_type=EventType.REENTRY,
                timestamp=timestamp,
                is_staff=is_staff,
                confidence=track.confidence,
                track_id=track.track_id,
            )
        elif not state.has_open_visit:
            collector.emit(
                camera_id=camera_id,
                visitor_id=visitor_id,
                event_type=EventType.ENTRY,
                timestamp=timestamp,
                is_staff=is_staff,
                confidence=track.confidence,
                track_id=track.track_id,
            )
        state.has_open_visit = True
        state.exited_once = False
    elif kind == "EXIT" and state.has_open_visit:
        collector.emit(
            camera_id=camera_id,
            visitor_id=visitor_id,
            event_type=EventType.EXIT,
            timestamp=timestamp,
            is_staff=is_staff,
            confidence=track.confidence,
            track_id=track.track_id,
        )
        state.has_open_visit = False
        state.exited_once = True


def _process_entry_line(
    track: Track,
    state: TrackZoneState,
    camera_zones: CameraZones,
    collector: EventCollector,
    *,
    camera_id: str,
    store_id: str,
    timestamp,
    is_staff: bool,
) -> None:
    """Directed line crossing on CAM_ENTRY (primary when it fires)."""
    if not camera_zones.entry_line:
        return
    p1 = tuple(camera_zones.entry_line["p1"])
    p2 = tuple(camera_zones.entry_line["p2"])
    inbound_positive = camera_zones.entry_line.get("inbound_side", "interior") == "interior"
    curr = line_side(p1, p2, track.centroid)
    crossing = line_crossing(state.line_side_value, curr, inbound_positive=inbound_positive)
    state.line_side_value = curr
    if crossing == "ENTRY":
        _emit_entry_exit(
            collector,
            camera_id=camera_id,
            store_id=store_id,
            track=track,
            state=state,
            timestamp=timestamp,
            is_staff=is_staff,
            kind="ENTRY",
        )
    elif crossing == "EXIT":
        _emit_entry_exit(
            collector,
            camera_id=camera_id,
            store_id=store_id,
            track=track,
            state=state,
            timestamp=timestamp,
            is_staff=is_staff,
            kind="EXIT",
        )


def _process_entry_threshold_zone(
    track: Track,
    state: TrackZoneState,
    camera_zones: CameraZones,
    collector: EventCollector,
    *,
    camera_id: str,
    store_id: str,
    timestamp,
    is_staff: bool,
) -> None:
    """
    Fallback/supplement for door geometry: debounced ENTRY_THRESHOLD occupancy.
    Handles cases where the configured line does not align perfectly with OSD perspective.
    """
    threshold_poly = None
    for zone in camera_zones.zones:
        if zone.zone_id == "ENTRY_THRESHOLD":
            threshold_poly = zone.polygon
            break
    if not threshold_poly:
        return

    inside = point_in_polygon(track.centroid, threshold_poly)
    key = "_threshold"
    if inside:
        state.pending_enter[key] = state.pending_enter.get(key, 0) + 1
        state.pending_exit[key] = 0
    else:
        state.pending_exit[key] = state.pending_exit.get(key, 0) + 1
        state.pending_enter[key] = 0

    if state.pending_enter.get(key, 0) >= TrackZoneState.DEBOUNCE_FRAMES and not state.has_open_visit:
        _emit_entry_exit(
            collector,
            camera_id=camera_id,
            store_id=store_id,
            track=track,
            state=state,
            timestamp=timestamp,
            is_staff=is_staff,
            kind="ENTRY",
        )
        state.pending_enter[key] = 0

    if state.pending_exit.get(key, 0) >= TrackZoneState.DEBOUNCE_FRAMES and state.has_open_visit:
        _emit_entry_exit(
            collector,
            camera_id=camera_id,
            store_id=store_id,
            track=track,
            state=state,
            timestamp=timestamp,
            is_staff=is_staff,
            kind="EXIT",
        )
        state.pending_exit[key] = 0


def _process_zones(
    track: Track,
    state: TrackZoneState,
    camera_zones: CameraZones,
    collector: EventCollector,
    *,
    camera_id: str,
    store_id: str,
    timestamp,
    timestamp_sec: float,
    is_staff: bool,
    queue_poly: list[list[float]] | None,
    all_tracks: list[Track],
    staff_ids: set[int],
) -> int:
    """Returns zone transition count delta for staff heuristic."""
    detected = set(camera_zones.zone_at_point(track.centroid))
    entered = zone_enter(state.inside_zones, detected)
    exited = zone_exit(state.inside_zones, detected)
    transitions = 0
    visitor_id = visitor_id_for_track(store_id, camera_id, track.track_id)

    for zone_id in entered:
        state.pending_enter[zone_id] = state.pending_enter.get(zone_id, 0) + 1
        state.pending_exit.pop(zone_id, None)

    for zone_id in exited:
        state.pending_exit[zone_id] = state.pending_exit.get(zone_id, 0) + 1
        state.pending_enter.pop(zone_id, None)

    confirmed_enter: list[str] = []
    for zone_id, count in list(state.pending_enter.items()):
        if count >= TrackZoneState.DEBOUNCE_FRAMES:
            confirmed_enter.append(zone_id)
            state.pending_enter.pop(zone_id, None)

    confirmed_exit: list[str] = []
    for zone_id, count in list(state.pending_exit.items()):
        if count >= TrackZoneState.DEBOUNCE_FRAMES:
            confirmed_exit.append(zone_id)
            state.pending_exit.pop(zone_id, None)

    skip_zones = {"ENTRY_THRESHOLD"} if camera_id == "CAM_ENTRY" else set()

    for zone_id in confirmed_enter:
        if zone_id in skip_zones:
            continue
        if zone_id not in state.inside_zones:
            state.inside_zones.add(zone_id)
            state.zone_entered_at[zone_id] = timestamp_sec
            state.last_dwell_at[zone_id] = timestamp_sec
            transitions += 1
            sku = camera_zones.sku_for_zone(zone_id)
            collector.emit(
                camera_id=camera_id,
                visitor_id=visitor_id,
                event_type=EventType.ZONE_ENTER,
                timestamp=timestamp,
                zone_id=zone_id,
                is_staff=is_staff,
                confidence=track.confidence,
                track_id=track.track_id,
                sku_zone=sku,
            )
            if zone_id == "BILLING_COUNTER":
                state.reached_counter = True

    for zone_id in confirmed_exit:
        if zone_id in skip_zones:
            continue
        if zone_id in state.inside_zones:
            entered_at = state.zone_entered_at.pop(zone_id, timestamp_sec)
            dwell_ms = int(max(0.0, (timestamp_sec - entered_at) * 1000))
            state.inside_zones.discard(zone_id)
            state.last_dwell_at.pop(zone_id, None)
            transitions += 1
            sku = camera_zones.sku_for_zone(zone_id)
            collector.emit(
                camera_id=camera_id,
                visitor_id=visitor_id,
                event_type=EventType.ZONE_EXIT,
                timestamp=timestamp,
                zone_id=zone_id,
                dwell_ms=dwell_ms,
                is_staff=is_staff,
                confidence=track.confidence,
                track_id=track.track_id,
                sku_zone=sku,
            )

    for zone_id in list(state.inside_zones):
        last = state.last_dwell_at.get(zone_id, timestamp_sec)
        if timestamp_sec - last >= TrackZoneState.DWELL_INTERVAL_SEC:
            sku = camera_zones.sku_for_zone(zone_id)
            collector.emit(
                camera_id=camera_id,
                visitor_id=visitor_id,
                event_type=EventType.ZONE_DWELL,
                timestamp=timestamp,
                zone_id=zone_id,
                dwell_ms=30000,
                is_staff=is_staff,
                confidence=track.confidence,
                track_id=track.track_id,
                sku_zone=sku,
            )
            state.last_dwell_at[zone_id] = timestamp_sec

    if queue_poly and camera_id == "CAM_BILLING":
        track_points = [
            (t.centroid, (t.track_id in staff_ids))
            for t in all_tracks
        ]
        depth = queue_depth(track_points, queue_poly)
        in_queue = "BILLING_QUEUE" in detected
        if in_queue and not state.queue_joined and depth >= 1:
            collector.emit(
                camera_id=camera_id,
                visitor_id=visitor_id,
                event_type=EventType.BILLING_QUEUE_JOIN,
                timestamp=timestamp,
                zone_id="BILLING_QUEUE",
                is_staff=is_staff,
                confidence=track.confidence,
                track_id=track.track_id,
                queue_depth=depth,
                sku_zone="QUEUE",
            )
            state.queue_joined = True
        if state.queue_joined and not in_queue and not state.reached_counter:
            collector.emit(
                camera_id=camera_id,
                visitor_id=visitor_id,
                event_type=EventType.BILLING_QUEUE_ABANDON,
                timestamp=timestamp,
                zone_id="BILLING_QUEUE",
                is_staff=is_staff,
                confidence=track.confidence,
                track_id=track.track_id,
                queue_depth=max(0, depth),
                sku_zone="QUEUE",
            )
            state.queue_joined = False

    state.zone_transition_count += transitions
    return transitions


def process_video(
    video_path: Path,
    camera_config: dict,
    layout: dict,
    collector: EventCollector,
    *,
    frame_stride: int = 2,
    debug_dir: Path | None = None,
    debug_interval: int = 45,
    conf: float = 0.35,
    max_frames: int = 0,
) -> VideoSummary:
    camera_id = camera_config["camera_id"]
    store_id = layout["store_id"]
    camera_zones = CameraZones.from_config(camera_config)
    anchor = parse_anchor(camera_config["timestamp_anchor"])
    on_backroom = camera_id == "CAM_BACKROOM"

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    tracker = ByteTracker(frame_rate=max(int(fps), 1))
    staff_clf = StaffClassifier(camera_id=camera_id)
    track_states: dict[int, TrackZoneState] = {}
    queue_poly = None
    for zone in camera_zones.zones:
        if zone.zone_id == "BILLING_QUEUE":
            queue_poly = zone.polygon
            break

    frame_idx = 0
    processed = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    limit = total_frames if max_frames <= 0 else min(total_frames, max_frames)

    while frame_idx < limit:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_idx % frame_stride != 0:
            frame_idx += 1
            continue

        staff_clf.register_frame()
        detections = detect_persons(frame, conf=conf)
        tracks = tracker.update(detections)
        timestamp = frame_to_timestamp(anchor, frame_idx, fps)
        timestamp_sec = frame_idx / fps

        provisional_staff: set[int] = set()
        if on_backroom:
            provisional_staff = {t.track_id for t in tracks}

        for track in tracks:
            state = track_states.setdefault(track.track_id, TrackZoneState())
            is_staff = track.track_id in provisional_staff

            if camera_id == "CAM_ENTRY":
                _process_entry_line(
                    track,
                    state,
                    camera_zones,
                    collector,
                    camera_id=camera_id,
                    store_id=store_id,
                    timestamp=timestamp,
                    is_staff=is_staff,
                )
                _process_entry_threshold_zone(
                    track,
                    state,
                    camera_zones,
                    collector,
                    camera_id=camera_id,
                    store_id=store_id,
                    timestamp=timestamp,
                    is_staff=is_staff,
                )

            delta = _process_zones(
                track,
                state,
                camera_zones,
                collector,
                camera_id=camera_id,
                store_id=store_id,
                timestamp=timestamp,
                timestamp_sec=timestamp_sec,
                is_staff=is_staff,
                queue_poly=queue_poly,
                all_tracks=tracks,
                staff_ids=provisional_staff,
            )
            staff_clf.observe(
                track.track_id,
                zone_transition_delta=delta,
                on_backroom_camera=on_backroom,
            )

        if debug_dir and processed % debug_interval == 0:
            save_debug_frame(
                frame,
                camera_id,
                frame_idx,
                tracks,
                camera_zones,
                debug_dir,
                provisional_staff,
            )

        processed += 1
        if processed % 50 == 0:
            logger.info("%s frame %s/%s tracks=%s", camera_id, frame_idx, limit, len(tracks))

        frame_idx += 1

    cap.release()

    staff_ids = staff_clf.finalize()
    if on_backroom:
        staff_ids = set(staff_clf.tracks.keys())

    staff_keys = {(camera_id, tid) for tid in staff_ids}
    collector.apply_staff_flags(staff_keys)

    counts = {}
    for event in collector.events:
        if event["camera_id"] != camera_id:
            continue
        et = event["event_type"]
        counts[et] = counts.get(et, 0) + 1

    return VideoSummary(
        camera_id=camera_id,
        video_file=video_path.name,
        frames_processed=processed,
        tracks_seen=len(track_states),
        staff_tracks=len(staff_ids),
        events_by_type=counts,
    )
