# Design

This document summarizes the current architecture and data flow for the Store Intelligence application.

## Architecture

- **FastAPI API** handles event ingestion, analytics queries, funneling, heatmap aggregation, and anomaly detection.
- **SQLite persistence** stores `stores`, `events`, `sessions`, `transactions`, and `metrics`.
- **CV pipeline** processes CCTV video with `YOLOv8n` for person detection, `ByteTrack` for tracking, and geometry-based zone rules for events.
- **Streamlit dashboard** displays live metrics, funnel state, heatmap scores, and anomalies.

## Event Flow

1. The pipeline produces challenge events in JSONL format using `pipeline/events.py`.
2. The API ingests events via `/events/ingest`.
3. Ingestion persists events, builds sessions, flags staff, and updates conversion state.
4. Analytics endpoints aggregate session and event data for metrics, funnel, heatmap, and anomalies.

## Data Flow

- `data/layouts/store_layout.json` defines camera zones, entry lines, and store metadata.
- `data/videos/*.mp4` are processed by `pipeline/run_pipeline.py`.
- `output/events.jsonl` is the pipeline output for ingestion.
- `data/transactions/brigade_pos.csv` is loaded into `transactions` and correlated with session billing events.

## Detection Pipeline

- `pipeline/detect.py` uses `YOLOv8n` and filters person detections to class 0.
- `pipeline/tracker.py` maintains stable track IDs and centroid history with `ByteTrack`.
- `pipeline/zones.py` evaluates polygon membership, line crossing, queue depth, and zone enters/exits.
- `pipeline/processor.py` converts detections into challenge events: `ENTRY`, `EXIT`, `ZONE_ENTER`, `ZONE_EXIT`, `ZONE_DWELL`, `BILLING_QUEUE_JOIN`, and `BILLING_QUEUE_ABANDON`.
