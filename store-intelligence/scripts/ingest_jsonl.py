#!/usr/bin/env python3
"""POST events.jsonl to the API in batches of 500."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="output/events.jsonl")
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    total_accepted = 0
    with httpx.Client(timeout=120.0) as client:
        for i in range(0, len(events), args.batch_size):
            batch = events[i : i + args.batch_size]
            resp = client.post(f"{args.api}/events/ingest", json={"events": batch})
            resp.raise_for_status()
            body = resp.json()
            total_accepted += body["accepted"]
            print(f"Batch {i // args.batch_size + 1}: {body}")

    print(f"Total accepted: {total_accepted} / {len(events)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
