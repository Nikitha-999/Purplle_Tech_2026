# Store Intelligence API

Purplle Store Intelligence Challenge — Phase 3.1 scaffold (API + database + health).

## Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)

## Quick start (local)

```bash
cd store-intelligence
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
mkdir var
set DATABASE_URL=sqlite:///./var/store_intelligence.db
set STORE_LAYOUT_PATH=data/layouts/store_layout.json
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Quick start (Docker)

```bash
cd store-intelligence
docker compose up --build
```

## Verify

```bash
curl http://localhost:8000/health
curl http://localhost:8000/
pytest
python -m pipeline.run_pipeline --layout data/layouts/store_layout.json
```

## Data layout

Place challenge assets under `data/`:

- `data/videos/*.mp4` — CCTV clips
- `data/transactions/brigade_pos.csv` — POS export
- `data/layouts/store_layout.json` — zone definitions (included)

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/events/ingest` | Batch ingest (max 500), idempotent |
| GET | `/stores/{id}/metrics?date=YYYY-MM-DD` | Visitors, conversion, dwell, queue |
| GET | `/stores/{id}/funnel?date=YYYY-MM-DD` | Session funnel |
| GET | `/stores/{id}/heatmap?date=YYYY-MM-DD` | Zone visit counts, dwell, confidence |
| GET | `/stores/{id}/anomalies?date=YYYY-MM-DD` | Rule-based operational anomalies |
| GET | `/health` | Service and per-store feed status |
| GET | `/docs` | OpenAPI UI |

### Sample workflow (no CV required)

```bash
curl -X POST http://localhost:8000/events/ingest \
  -H "Content-Type: application/json" \
  -d @data/samples/events_sample.json

curl "http://localhost:8000/stores/ST1008/metrics?date=2026-04-10"
curl "http://localhost:8000/stores/ST1008/funnel?date=2026-04-10"

deploy-frontend "https://purplle-tech-challenge-2026-xi.vercel.app/"
deploy-backend "https://purplle-tech-2026-1.onrender.com/"
```

Use `date=2026-04-10` to align with the bundled POS CSV.

## Detection pipeline (Phase 3.5)

```bash
pip install -r requirements.txt -r requirements-pipeline.txt
python -m pipeline.run_pipeline
# → output/events.jsonl, output/debug/<camera>/
curl -X POST http://localhost:8000/events/ingest -H "Content-Type: application/json" \
  -d "{\"events\": $(python -c "import json;print(json.dumps([json.loads(l) for l in open('output/events.jsonl')]))")}"
```

Or ingest line-by-line with a small script. For large files, POST in batches of ≤500.
## Dashboard

Launch the Streamlit dashboard after the API is running:

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

Open the dashboard at `http://localhost:8501` and set `ST1008` as the store ID. The dashboard polls the API every 5 seconds.
