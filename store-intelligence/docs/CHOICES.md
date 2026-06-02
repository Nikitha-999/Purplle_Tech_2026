# Engineering choices

This document explains the main tradeoffs made in the Store Intelligence pipeline.

## Why YOLOv8n

- `YOLOv8n` is lightweight and effective for real-time person detection.
- It supports CPU inference and leverages GPU if available.
- The challenge dataset is short and focused; a small model balances speed and precision without requiring a large CV stack.

## Why SQLite

- SQLite is simple to configure and works well for local challenge submission.
- The schema is lightweight and supports fast time-based queries for analytics.
- It removes external database dependencies and enables reproducible evaluation.

## Why ByteTrack

- `ByteTrack` provides stable multi-object tracking IDs across frames.
- Stable IDs are important for visitor session tracking, queue analysis, and zone dwell calculations.
- The implementation retains centroid history for trajectory-based heuristics.

## Why Rule-Based Anomalies

- The anomaly rules are deterministic, explainable, and safe for a challenge submission.
- `QUEUE_SPIKE` detects unusually high billing queue activity.
- `CONVERSION_DROP` identifies low conversion performance relative to observed visitor traffic.
- `DEAD_ZONE` flags store areas with no recorded non-staff visits.
