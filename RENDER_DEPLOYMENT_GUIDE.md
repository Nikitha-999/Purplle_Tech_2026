# 🚀 Render Deployment Guide - Store Intelligence Platform

**Analysis Date:** June 3, 2026  
**Project:** Purplle Store Intelligence (Phase 3.1 - API + Frontend Dashboard)

---

## 📋 REPOSITORY ANALYSIS

### A. Framework & Technology Stack

| Component | Technology | Version | Entry Point |
|-----------|-----------|---------|------------|
| **Backend** | FastAPI | 0.115.6 | `app/main.py` |
| **Backend Server** | Uvicorn | 0.32.1 | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| **Frontend** | React + TypeScript | 18.3.1 / 5.6.2 | `src/main.tsx` |
| **Frontend Build Tool** | Vite | 5.4.1 | `tsc && vite build` → `dist/` |
| **Database** | SQLite | - | `sqlite:////app/var/store_intelligence.db` |
| **ORM** | SQLAlchemy | 2.0.36 | `app/database.py` |
| **Dashboard** | Streamlit | 1.29.0 | `dashboard/app.py` (optional) |

---

## 🔍 DEPLOYMENT CONFIGURATION ANALYSIS

### Backend (FastAPI + Uvicorn)

**Source File:** [app/main.py](app/main.py#L1)

```python
# CORS Configuration (FROM app/main.py:73)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # ⚠️ HARDCODED
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Current Dockerfile:** [Dockerfile](Dockerfile) ✅ **Production-Ready**
- Uses `python:3.11-slim` (good)
- Sets PYTHONUNBUFFERED=1
- Includes health check
- Exposes port 8000
- Does NOT include requirements-pipeline.txt (correct for API-only deployment)

**Port:** `8000`

**Health Check:** `GET /health` (built-in, returns HealthResponse)

---

### Frontend (React + Vite)

**Source File:** [frontend/package.json](frontend/package.json)

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",  // Outputs to dist/
    "preview": "vite preview"
  }
}
```

**API Configuration:** [frontend/src/services/api.ts](frontend/src/services/api.ts#L8)

```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',  // ✅ ENVIRONMENT VARIABLE
  timeout: 12000,
});
```

✅ **Good:** Uses `VITE_API_URL` environment variable (no hardcoded URLs)

**Build Output Directory:** `dist/` (standard Vite output)

**Node Version:** 18+ (compatible with Vite 5.4.1)

---

## 📦 DEPENDENCIES ANALYSIS

### Backend Dependencies (requirements.txt)

```
fastapi==0.115.6
uvicorn[standard]==0.32.1
sqlalchemy==2.0.36
pydantic==2.10.3
pydantic-settings==2.6.1
python-multipart==0.0.17
httpx==0.28.1
streamlit==1.29.0
pytest==8.3.4
pytest-asyncio==0.24.0
```

**Optional (NOT for API deployment):**
```
# requirements-pipeline.txt
ultralytics>=8.3.0        # YOLOv8 (large, CV only)
torch>=2.1.0              # PyTorch (large, CV only)
torchvision>=0.16.0       # Vision (large, CV only)
opencv-python-headless    # CV only
```

⚠️ **Note:** YOLOv8 model file `yolov8n.pt` (64 MB) is in repo root - excluded from API deployment

### Frontend Dependencies

```json
{
  "dependencies": [
    "react@18.3.1",
    "react-dom@18.3.1",
    "@tanstack/react-query@5.0.0",
    "axios@1.7.0",
    "react-router-dom@6.16.0",
    "recharts@2.9.0",
    "tailwindcss@3.4.4"
  ]
}
```

**Total size:** ~650 MB (node_modules) - normal for React app

---

## 🐳 EXISTING DOCKER CONFIGURATION

**File:** [Dockerfile](Dockerfile)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data

RUN mkdir -p /app/var

ENV DATABASE_URL=sqlite:////app/var/store_intelligence.db \
    STORE_LAYOUT_PATH=/app/data/layouts/store_layout.json

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

✅ **Assessment:** Production-ready for backend

---

## ⚠️ DEPLOYMENT BLOCKERS IDENTIFIED

### 🔴 CRITICAL ISSUES

#### 1. **Hardcoded CORS Origins** [app/main.py:73]
- Current: `allow_origins=["http://localhost:5173", "http://localhost:3000"]`
- **Impact:** Frontend will get CORS error when calling production backend
- **Solution:** Update to accept production URLs or use environment variable

#### 2. **SQLite Database on Ephemeral Filesystem**
- SQLite stores data in `/app/var/store_intelligence.db`
- Render's free tier has **ephemeral filesystem** (data lost on redeploy)
- **Solution:** Use Render PostgreSQL or configure persistent disk

#### 3. **Data Files Path Reference**
- `STORE_LAYOUT_PATH=/app/data/layouts/store_layout.json`
- `POS_CSV_PATH=/app/data/transactions/brigade_pos.csv`
- Files must be committed to repo or downloaded at startup

#### 4. **Large Model File**
- `yolov8n.pt` (64 MB) in repo root
- Included in Docker build, increases build time
- **Solution:** Add to `.dockerignore`

#### 5. **No render.yaml** (Multi-service coordination)
- Backend and frontend need separate services
- Should be orchestrated in `render.yaml`

---

### 🟡 WARNINGS

1. **Database Initialization**
   - `init_db()` called at startup (lifespan)
   - Requires `data/layouts/store_layout.json` to exist
   - If missing, app will crash

2. **POS CSV Loading**
   - Tries to load `data/transactions/brigade_pos.csv` at startup
   - CSV file must exist in build context

3. **Environment Variables Not Documented**
   - No `.env.example` provided
   - Required vars: `DATABASE_URL`, `STORE_LAYOUT_PATH`, `POS_CSV_PATH`

---

## ✅ DEPLOYMENT CONFIGURATIONS

### A. BACKEND SERVICE - Render Web Service

**Service Type:** Web Service (Docker)

```
┌─────────────────────────────────────────┐
│ Name                                    │ store-intelligence-backend
├─────────────────────────────────────────┤
│ Environment                             │ Docker
├─────────────────────────────────────────┤
│ Region                                  │ Oregon (US West)
├─────────────────────────────────────────┤
│ Repository                              │ Your GitHub repo
├─────────────────────────────────────────┤
│ Branch                                  │ main
├─────────────────────────────────────────┤
│ Root Directory                          │ store-intelligence
├─────────────────────────────────────────┤
│ Dockerfile Path                         │ ./Dockerfile
├─────────────────────────────────────────┤
│ Instance Type                           │ Standard ($25/mo) or Starter ($7/mo)
│                                         │ (Free tier = limited CPU)
├─────────────────────────────────────────┤
│ Build Command                           │ [Auto-detected from Dockerfile]
├─────────────────────────────────────────┤
│ Start Command                           │ [Auto-detected from Dockerfile]
└─────────────────────────────────────────┘
```

**Environment Variables:**

| Variable | Value | Source | Required |
|----------|-------|--------|----------|
| `DATABASE_URL` | `postgresql://user:pass@render-postgres-url/db` | Render PostgreSQL | ✅ YES |
| `STORE_LAYOUT_PATH` | `/app/data/layouts/store_layout.json` | Dockerfile default | ✅ YES |
| `POS_CSV_PATH` | `/app/data/transactions/brigade_pos.csv` | Dockerfile default | ✅ YES |
| `LOG_LEVEL` | `INFO` | Optional | ❌ NO |
| `STALE_FEED_MINUTES` | `10` | Optional | ❌ NO |
| `PYTHONUNBUFFERED` | `1` | Dockerfile | ✅ YES |

**Health Check URL:** `https://<backend-url>/health`

**Port:** 8000 (Render maps to 443 HTTPS)

---

### B. FRONTEND SERVICE - Render Static Site or Web Service

**Option B1: Render Static Site (Recommended - Cheaper)**

```
┌─────────────────────────────────────────┐
│ Name                                    │ store-intelligence-frontend
├─────────────────────────────────────────┤
│ Environment                             │ Static Site
├─────────────────────────────────────────┤
│ Region                                  │ Oregon (US West)
├─────────────────────────────────────────┤
│ Repository                              │ Your GitHub repo
├─────────────────────────────────────────┤
│ Branch                                  │ main
├─────────────────────────────────────────┤
│ Root Directory                          │ store-intelligence/frontend
├─────────────────────────────────────────┤
│ Build Command                           │ npm install && npm run build
├─────────────────────────────────────────┤
│ Publish Directory                       │ dist
└─────────────────────────────────────────┘
```

**Environment Variables:**

| Variable | Value | Note |
|----------|-------|------|
| `VITE_API_URL` | `https://store-intelligence-backend.onrender.com` | Backend URL |
| `VITE_STORE_ID` | `ST1008` | Default store |

**Option B2: Render Web Service (if you need server-side rendering)**

```
┌─────────────────────────────────────────┐
│ Name                                    │ store-intelligence-frontend
├─────────────────────────────────────────┤
│ Environment                             │ Docker (Node)
├─────────────────────────────────────────┤
│ Root Directory                          │ store-intelligence/frontend
├─────────────────────────────────────────┤
│ Dockerfile Path                         │ ./Dockerfile.frontend (needs creation)
├─────────────────────────────────────────┤
│ Instance Type                           │ Free or Starter
└─────────────────────────────────────────┘
```

---

## 📄 render.yaml (Multi-Service Configuration)

**File:** Create at `render.yaml` (repo root)

```yaml
services:
  - type: web
    name: store-intelligence-backend
    env: docker
    region: oregon
    rootDir: store-intelligence
    dockerfilePath: ./Dockerfile
    autoDeploy: true
    envVars:
      - key: DATABASE_URL
        scope: build
        sync: false
      - key: STORE_LAYOUT_PATH
        value: /app/data/layouts/store_layout.json
      - key: POS_CSV_PATH
        value: /app/data/transactions/brigade_pos.csv

  - type: static_site
    name: store-intelligence-frontend
    env: static
    region: oregon
    rootDir: store-intelligence/frontend
    buildCommand: npm install && npm run build
    staticPublishPath: ./dist
    autoDeploy: true
    envVars:
      - key: VITE_API_URL
        scope: build
        value: https://store-intelligence-backend.onrender.com
      - key: VITE_STORE_ID
        scope: build
        value: ST1008
```

---

## 🐳 CORRECTED DOCKERFILES

### Backend Dockerfile (Corrected)

**File:** [Dockerfile](Dockerfile)

The existing Dockerfile is **production-ready**. However, add `.dockerignore` to exclude large files:

**Create: `.dockerignore`**

```
yolov8n.pt
__pycache__
.pytest_cache
.git
.gitignore
.env
*.pyc
*.pyo
node_modules
frontend/dist
frontend/node_modules
output/
var/
.venv
```

---

### Frontend Dockerfile (NEW - if deploying as Web Service)

**Create: `store-intelligence/frontend/Dockerfile`**

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install simple HTTP server
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /app/dist ./dist

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/index.html || exit 1

# Serve on port 3000
EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
```

---

## 🔧 REQUIRED FIXES BEFORE DEPLOYMENT

### 1. Update CORS Configuration

**File:** [app/main.py](app/main.py#L73)

Replace hardcoded localhost origins with environment variable:

```python
# BEFORE (app/main.py:73)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AFTER (app/main.py:73)
from app.config import get_settings

settings = get_settings()
cors_origins = settings.cors_origins.split(",") if settings.cors_origins else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Update config.py

**File:** [app/config.py](app/config.py)

Add CORS origins setting:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./var/store_intelligence.db"
    store_layout_path: str = "data/layouts/store_layout.json"
    pos_csv_path: str = "data/transactions/brigade_pos.csv"
    log_level: str = "INFO"
    stale_feed_minutes: int = 10
    cors_origins: str = "http://localhost:5173,http://localhost:3000"  # NEW
```

### 3. Create .env.example

**File:** Create `store-intelligence/.env.example`

```env
# Database
DATABASE_URL=sqlite:///./var/store_intelligence.db

# Paths
STORE_LAYOUT_PATH=data/layouts/store_layout.json
POS_CSV_PATH=data/transactions/brigade_pos.csv

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Logging
LOG_LEVEL=INFO

# Business logic
STALE_FEED_MINUTES=10
```

### 4. Create .dockerignore

**File:** Create `store-intelligence/.dockerignore`

```
yolov8n.pt
__pycache__
.pytest_cache
.git
.gitignore
.env
*.pyc
*.pyo
node_modules
frontend/dist
frontend/node_modules
output/
var/
.venv
*.md
tests/
.vscode
```

---

## 🚀 DEPLOYMENT STEP-BY-STEP

### Step 1: Prepare Repository

```bash
cd store-intelligence

# Add .dockerignore
cat > .dockerignore << 'EOF'
yolov8n.pt
__pycache__
.pytest_cache
.git
.gitignore
.env
*.pyc
*.pyo
node_modules
frontend/dist
frontend/node_modules
output/
var/
.venv
*.md
tests/
.vscode
EOF

# Add .env.example
cat > .env.example << 'EOF'
DATABASE_URL=sqlite:///./var/store_intelligence.db
STORE_LAYOUT_PATH=data/layouts/store_layout.json
POS_CSV_PATH=data/transactions/brigade_pos.csv
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
LOG_LEVEL=INFO
STALE_FEED_MINUTES=10
EOF

git add .dockerignore .env.example
git commit -m "chore: add deployment configs"
git push
```

### Step 2: Create Backend Service on Render

1. Go to https://render.com/dashboard
2. Click **New Web Service**
3. Connect GitHub repo
4. Fill form:
   - **Name:** `store-intelligence-backend`
   - **Environment:** `Docker`
   - **Region:** `Oregon`
   - **Root Directory:** `store-intelligence`
   - **Dockerfile Path:** `./Dockerfile`
   - **Instance Type:** `Starter` ($7/mo) or `Standard` ($25/mo)

5. Add Environment Variables:
   ```
   DATABASE_URL = postgresql://...render... (create PostgreSQL addon)
   STORE_LAYOUT_PATH = /app/data/layouts/store_layout.json
   POS_CSV_PATH = /app/data/transactions/brigade_pos.csv
   CORS_ORIGINS = https://<frontend-url>,https://store-intelligence-backend.onrender.com
   LOG_LEVEL = INFO
   ```

6. Click **Deploy**

### Step 3: Create Frontend Service on Render

1. Click **New Static Site** (or **New Web Service** if using Dockerfile)
2. Connect GitHub repo
3. Fill form:
   - **Name:** `store-intelligence-frontend`
   - **Environment:** `Static Site`
   - **Root Directory:** `store-intelligence/frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`

4. Add Environment Variables:
   ```
   VITE_API_URL = https://store-intelligence-backend.onrender.com
   VITE_STORE_ID = ST1008
   ```

5. Click **Deploy**

### Step 4: Configure Auto-Deploy

- Both services auto-deploy on GitHub push
- Frontend deploys when `store-intelligence/frontend/` changes
- Backend deploys when `store-intelligence/` changes

---

## 🔐 SECURITY CONSIDERATIONS

1. **CORS Origins:** Update to production URLs after deployment
2. **Environment Variables:** Never commit `.env` file
3. **Database:** Use Render PostgreSQL (managed), not SQLite
4. **API Keys:** Store in Render environment variables (encrypted)
5. **HTTPS:** Render enforces HTTPS by default ✅

---

## 📊 ESTIMATED COSTS

| Service | Type | Instance | Cost |
|---------|------|----------|------|
| Backend | Web | Starter | $7/mo |
| Frontend | Static Site | - | $0 |
| Database | PostgreSQL | Starter | $7/mo |
| **Total** | | | **~$14/mo** |

---

## ✅ DEPLOYMENT CHECKLIST

- [ ] Run `npm install && npm run build` in frontend/ locally (verify build works)
- [ ] Run `pip install -r requirements.txt && pytest` locally (verify tests pass)
- [ ] Commit `.dockerignore` and `.env.example`
- [ ] Push to GitHub
- [ ] Create Backend Web Service on Render
- [ ] Create Frontend Static Site on Render
- [ ] Test backend health endpoint: `https://<backend>.onrender.com/health`
- [ ] Test frontend loads: `https://<frontend>.onrender.com`
- [ ] Verify API calls work (check browser console for CORS)
- [ ] Update CORS_ORIGINS if needed

---

## 🐛 TROUBLESHOOTING

### Frontend shows "Cannot GET /"
- Build command didn't run or failed
- Check Build Logs in Render dashboard
- Verify `dist/` is the publish directory

### CORS Error in Browser Console
- Backend CORS_ORIGINS doesn't include frontend URL
- Update environment variable and redeploy

### "module not found" error
- `requirements.txt` incomplete
- Check pip install locally: `pip install -r requirements.txt && python -c "import app.main"`

### Health check failing
- Backend not responding on `/health`
- Check logs: `curl https://<backend>/health`
- Verify port 8000 mapped correctly

---

## 📞 NEXT STEPS

1. **Make code changes** (CORS config, environment variables)
2. **Test locally** with Docker: `docker build -t backend . && docker run -p 8000:8000 backend`
3. **Deploy to Render** using steps above
4. **Monitor logs** in Render dashboard
5. **Set up alerts** (optional) for deployment failures

