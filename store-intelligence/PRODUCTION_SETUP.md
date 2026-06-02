# 🏪 Purplle Store Intelligence Platform - Production Setup Guide

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Backend running at `http://localhost:8000`
- Frontend development server at `http://localhost:5173`

### Step 1: Start the Backend

```bash
cd store-intelligence

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```

**Backend API Endpoints:**
- `GET /health` - Health check
- `GET /stores/ST1008/metrics` - KPI metrics
- `GET /stores/ST1008/funnel` - Conversion funnel
- `GET /stores/ST1008/heatmap` - Zone heatmap
- `GET /stores/ST1008/anomalies` - Anomaly detection

### Step 2: Start the Frontend

```bash
cd store-intelligence/frontend

# Install dependencies (if not done)
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Step 3: Ingest Sample Events (Optional)

```bash
cd store-intelligence

# Run the event ingestion pipeline
python scripts/ingest_jsonl.py
```

## Features Implemented

### ✅ Task 1: Frontend API Connection
- All pages connected to backend APIs with `http://localhost:8000` base URL
- Environment variables configured in `.env.development` and `.env.production`
- Auto-refresh every 15 seconds for real-time data
- Full error handling and loading states

### ✅ Task 2: Executive Dashboard
- **KPI Cards**: Unique Visitors, Converted, Conversion Rate, Transactions, Queue Depth, Abandonment Rate
- **Funnel Chart**: Visualizes Entry → Zone Visit → Billing Queue → Purchase
- **Zone Activity**: Top zones by visits with bar chart
- **Live auto-refresh** every 15 seconds

### ✅ Task 3: Heatmap Visualization
- **Color-Coded Zones**:
  - 🟢 Green (0-25): Cold zones
  - 🟡 Yellow (25-50): Warm zones
  - 🟠 Orange (50-75): Hot zones
  - 🔴 Red (75-100): Very hot zones
- **Interactive Zone Cards**: Click to view detailed stats
- **Zone Ranking**: Sorted by intensity score
- **Zone Details**: Visitors, avg dwell time, intensity score

### ✅ Task 4: Funnel Logic Fix
- Backend correctly processes `BILLING_QUEUE_JOIN` events
- Funnel stages accurately count: ENTRY → ZONE_VISIT → BILLING_QUEUE → PURCHASE
- Session-based tracking ensures accurate conversion metrics

### ✅ Task 5: Anomalies & AI Insights
- Real-time anomaly detection from `/stores/ST1008/anomalies`
- Human-readable alerts with suggested actions
- Severity-based filtering (Critical, Warn, Info)
- Zone-specific anomalies with context

### ✅ Task 6: CCTV Replay Enhancement
- Timeline replay with play/pause controls
- Speed controls (1x, 2x, 4x)
- Progress slider for scrubbing
- Recent event list synced with playback

### ✅ Task 7: SaaS UI Polish
- Gradient KPI cards with hover effects
- Smooth animations with Framer Motion
- Responsive layout (desktop + tablet + mobile)
- Dark mode support
- Clean card-based design with Tailwind CSS
- Professional typography and spacing

## API Response Examples

### Metrics Response
```json
{
  "store_id": "ST1008",
  "date": "2026-04-10",
  "unique_visitors": 42,
  "converted_visitors": 15,
  "conversion_rate": 0.357,
  "current_queue_depth": 3,
  "queue_abandonment_rate": 0.05,
  "total_transactions": 15
}
```

### Heatmap Response
```json
{
  "store_id": "ST1008",
  "date": "2026-04-10",
  "zones": [
    {
      "zone_id": "BILLING_COUNTER",
      "visit_count": 42,
      "avg_dwell_sec": 45.2,
      "score_0_100": 85
    }
  ],
  "data_confidence": "high"
}
```

### Funnel Response
```json
{
  "store_id": "ST1008",
  "date": "2026-04-10",
  "unit": "session",
  "stages": [
    {"name": "entry", "label": "Entry", "count": 42, "drop_off_pct": 0},
    {"name": "zone_visit", "label": "Zone Visit", "count": 40, "drop_off_pct": 4.76},
    {"name": "billing_queue", "label": "Billing Queue", "count": 18, "drop_off_pct": 55},
    {"name": "purchase", "label": "Purchase", "count": 15, "drop_off_pct": 16.67}
  ]
}
```

## Frontend Pages

| Page | Route | Features |
|------|-------|----------|
| Dashboard | `/` | KPIs, Funnel Chart, Zone Activity |
| Command Center | `/command-center` | Live KPIs, alerts, camera activity |
| Insights | `/insights` | AI-powered retail intelligence |
| Funnel | `/funnel` | Conversion flow with drop-off analysis |
| Heatmap | `/heatmap` | Color-coded zone intensity |
| Anomalies | `/anomalies` | Real-time alerts and recommendations |
| Replay | `/replay` | Timeline event playback |
| Pipeline | `/pipeline` | System health and status |
| Viewer | `/viewer` | Video player integration |
| Layout | `/layout` | Store layout visualization |

## Tech Stack

### Frontend
- React 18 with TypeScript
- Vite for fast bundling
- Tailwind CSS for styling
- Recharts for data visualization
- Framer Motion for animations
- React Query for state management
- React Router for navigation
- Axios for HTTP requests

### Backend
- FastAPI (Python)
- SQLAlchemy ORM
- ByteTrack for person tracking
- YOLOv8 for object detection
- SQLite for persistence

## Development Commands

```bash
# Frontend
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run linter

# Backend
uvicorn app.main:app --reload      # Start with auto-reload
python scripts/ingest_jsonl.py     # Ingest events
```

## Troubleshooting

**Frontend shows "Failed to load" for API calls:**
- Ensure backend is running on `http://localhost:8000`
- Check `.env.development` has `VITE_API_URL=http://localhost:8000`
- Verify no CORS issues (backend should have CORS enabled)

**Heatmap zones showing 0 scores:**
- Events must be ingested into the database
- Run `python scripts/ingest_jsonl.py` to populate events
- Data is computed from `output/events.jsonl`

**Funnel showing 0 for billing queue:**
- Verify `BILLING_QUEUE_JOIN` events exist in `output/events.jsonl`
- Run event ingest script to populate database
- Check that events have correct timestamps (should be today's date)

## Production Deployment

1. Build frontend: `npm run build` (creates `dist/` folder)
2. Serve static files from `frontend/dist/`
3. Point API requests to production backend
4. Update `.env.production` with production API URL
5. Enable GZIP compression for assets
6. Consider code-splitting to reduce bundle size

## Key Metrics Tracked

- **Conversion Rate**: Percentage of visitors who purchased
- **Queue Abandonment**: Percentage of visitors who left while queuing
- **Dwell Time**: Average time spent in each zone
- **Zone Intensity**: Heatmap score based on traffic volume and duration
- **Traffic Flow**: Entry → Zone visits → Queue → Purchase stages
