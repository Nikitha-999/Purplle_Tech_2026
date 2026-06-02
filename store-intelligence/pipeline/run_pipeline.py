#!/usr/bin/env python3
"""Process all CCTV clips and write output/events.jsonl."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pipeline.detect import is_detection_available
from pipeline.events import EventCollector
from pipeline.processor import process_video
from pipeline.tracker import is_tracking_available
from pipeline.zones import load_store_layout


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Store Intelligence CV pipeline")
    parser.add_argument("--layout", default="data/layouts/store_layout.json")
    parser.add_argument("--videos-dir", default="data/videos")
    parser.add_argument("--output", default="output/events.jsonl")
    parser.add_argument("--debug-dir", default="output/debug")
    parser.add_argument("--frame-stride", type=int, default=2, help="Process every Nth frame")
    parser.add_argument("--conf", type=float, default=0.35, help="YOLO confidence threshold")
    parser.add_argument("--device", default="auto", help="auto | cpu | 0")
    parser.add_argument("--no-debug", action="store_true", help="Skip debug overlay frames")
    parser.add_argument("--max-frames", type=int, default=0, help="Limit frames per video (0=all)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not is_detection_available() or not is_tracking_available():
        print(
            "Missing CV dependencies. Install: pip install -r requirements-pipeline.txt",
            file=sys.stderr,
        )
        return 1

    if args.device != "auto":
        from pipeline import detect as detect_mod

        detect_mod._DEVICE = args.device if args.device != "cpu" else "cpu"

    layout_path = Path(args.layout)
    # Resolve relative paths against the package root so CLI calls from repo root work
    if not layout_path.is_absolute():
        layout_path = _ROOT / layout_path
    if not layout_path.is_file():
        print(f"Layout not found: {layout_path}", file=sys.stderr)
        return 1

    layout = load_store_layout(layout_path)
    videos_dir = Path(args.videos_dir)
    if not videos_dir.is_absolute():
        videos_dir = _ROOT / videos_dir
    store_id = layout["store_id"]
    collector = EventCollector(store_id=store_id)

    debug_dir = None if args.no_debug else Path(args.debug_dir)
    if debug_dir and not debug_dir.is_absolute():
        debug_dir = _ROOT / debug_dir
    summaries = []

    for camera in layout.get("cameras", []):
        video_name = camera["video_file"]
        video_path = videos_dir / video_name
        if not video_path.is_file():
            print(f"Warning: missing video {video_path}", file=sys.stderr)
            continue
        print(f"Processing {camera['camera_id']} <- {video_name} ...", flush=True)
        summary = process_video(
            video_path,
            camera,
            layout,
            collector,
            frame_stride=args.frame_stride,
            debug_dir=debug_dir,
            conf=args.conf,
            max_frames=args.max_frames,
        )
        summaries.append(summary)
        print(
            f"  frames={summary.frames_processed} tracks={summary.tracks_seen} "
            f"staff_tracks={summary.staff_tracks} events={summary.events_by_type}"
        )

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = _ROOT / output_path
    total = collector.write_jsonl(output_path)
    counts = collector.counts_by_type()

    visitors = {
        e["visitor_id"]
        for e in collector.events
        if not e.get("is_staff") and e["event_type"] == "ENTRY"
    }
    staff_visitors = {
        e["visitor_id"]
        for e in collector.events
        if e.get("is_staff")
    }

    zone_events = sum(
        counts.get(t, 0)
        for t in ("ZONE_ENTER", "ZONE_EXIT", "ZONE_DWELL")
    )
    billing_events = sum(
        counts.get(t, 0)
        for t in ("BILLING_QUEUE_JOIN", "BILLING_QUEUE_ABANDON")
    )

    print("\n========== Pipeline Summary ==========")
    print(f"Events written: {total} → {output_path}")
    print(f"Visitors detected (ENTRY, non-staff): {len(visitors)}")
    print(f"Staff-related tracks flagged: {len(staff_visitors)}")
    print(f"ENTRY events: {counts.get('ENTRY', 0)}")
    print(f"EXIT events: {counts.get('EXIT', 0)}")
    print(f"REENTRY events: {counts.get('REENTRY', 0)}")
    print(f"ZONE events: {zone_events}")
    print(f"Billing queue events: {billing_events}")
    if debug_dir:
        print(f"Debug overlays: {debug_dir}/<CAMERA_ID>/")
    print("======================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
