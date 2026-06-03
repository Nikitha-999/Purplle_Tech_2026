# 🚀 Render Deployment - Quick Reference

## Pre-Deployment Checklist

```bash
# 1. Verify backend builds locally
cd store-intelligence
docker build -t store-api .

# 2. Verify frontend builds locally
cd frontend
npm install
npm run build
cd ..

# 3. Verify tests pass
pip install -r requirements.txt
pytest

# 4. Commit files to git
git add -A
git commit -m "chore: add render deployment configs"
git push origin main
```

## Backend Deployment (Render Web Service)

### Service Details

| Setting | Value |
|---------|-------|
| **Name** | `store-intelligence-backend` |
| **Environment** | Docker |
| **Region** | Oregon |
| **Repository** | Your GitHub repo |
| **Branch** | main |
| **Root Directory** | `store-intelligence` |
| **Dockerfile Path** | `./Dockerfile` |
| **Instance Type** | Starter ($7/mo) or Standard ($25/mo) |

### Environment Variables

Add these in Render Dashboard → Environment:

```
DATABASE_URL              postgresql://...    (create Render PostgreSQL addon)
STORE_LAYOUT_PATH         /app/data/layouts/store_layout.json
POS_CSV_PATH              /app/data/transactions/brigade_pos.csv
CORS_ORIGINS              https://store-intelligence-frontend.onrender.com
LOG_LEVEL                 INFO
PYTHONUNBUFFERED          1
```

### Verification

After deployment:

```bash
# Test health endpoint
curl https://store-intelligence-backend.onrender.com/health

# Should return:
# {
#   "status": "healthy",
#   ...
# }
```

---

## Frontend Deployment (Render Static Site - RECOMMENDED)

### Service Details

| Setting | Value |
|---------|-------|
| **Name** | `store-intelligence-frontend` |
| **Environment** | Static Site |
| **Region** | Oregon |
| **Repository** | Your GitHub repo |
| **Branch** | main |
| **Root Directory** | `store-intelligence/frontend` |
| **Build Command** | `npm install && npm run build` |
| **Publish Directory** | `dist` |

### Environment Variables

Add these in Render Dashboard → Environment:

```
VITE_API_URL         https://store-intelligence-backend.onrender.com
VITE_STORE_ID        ST1008
```

### Verification

After deployment:

```bash
# Visit the frontend URL
https://store-intelligence-frontend.onrender.com

# Verify:
# 1. Page loads without "Cannot GET /"
# 2. No CORS errors in browser console
# 3. API calls work (check Network tab)
```

---

## Deployment Steps (UI)

### Backend

1. Go to https://render.com/dashboard
2. **New +** → **Web Service**
3. Connect your GitHub repository
4. Fill in:
   - **Name:** `store-intelligence-backend`
   - **Environment:** `Docker`
   - **Region:** `Oregon`
   - **Root Directory:** `store-intelligence`
   - **Dockerfile Path:** `./Dockerfile`
   - **Instance Type:** `Starter`
5. **Create Web Service**
6. Go to **Environment** tab and add variables above
7. **Deploy** (auto-deploys on push)

### Frontend

1. **New +** → **Static Site**
2. Connect your GitHub repository
3. Fill in:
   - **Name:** `store-intelligence-frontend`
   - **Environment:** `Static Site`
   - **Region:** `Oregon`
   - **Root Directory:** `store-intelligence/frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`
4. **Create Static Site**
5. Go to **Environment** tab and add variables above
6. **Deploy** (auto-deploys on push)

---

## Using render.yaml (Alternative - Command Line)

If you have Render CLI installed:

```bash
render deploy render.yaml
```

---

## Files Created for Deployment

✅ Created:
- `store-intelligence/.dockerignore` - Excludes large files from build
- `store-intelligence/.env.example` - Documents required environment variables
- `store-intelligence/frontend/Dockerfile` - Frontend deployment (if needed)
- `render.yaml` - Multi-service configuration

✅ Modified:
- `store-intelligence/app/config.py` - Added `cors_origins` setting
- `store-intelligence/app/main.py` - Uses environment variable for CORS

---

## Troubleshooting

### Frontend shows "Cannot GET /"

**Cause:** Build failed or dist directory not published

**Fix:**
```bash
# Check build logs in Render dashboard
# Re-run build:
cd store-intelligence/frontend
npm install
npm run build

# Verify dist/ exists
ls -la dist/

# Commit and push
git add dist/ (if tracking)
git push
```

### CORS Error in Browser

**Cause:** Frontend URL not in backend CORS_ORIGINS

**Fix:**
1. Copy frontend URL from Render dashboard
2. Backend → Environment → Edit `CORS_ORIGINS`
3. Add frontend URL: `https://store-intelligence-frontend.onrender.com`
4. **Deploy** backend

### Backend returns 502 Bad Gateway

**Cause:** Build failed or app crashed at startup

**Fix:**
1. Check **Logs** in Render dashboard
2. Look for database initialization errors
3. Verify `STORE_LAYOUT_PATH` and `POS_CSV_PATH` exist in repo

### "Module not found" error

**Cause:** requirements.txt incomplete

**Fix:**
```bash
pip install -r requirements.txt
python -c "import app.main"  # Should not error
git add requirements.txt
git push
```

---

## Estimated Monthly Cost

```
Backend (Starter):     $7
Frontend (Static):     $0
PostgreSQL (Starter):  $7
───────────────────────
Total:                $14/month
```

---

## Next Steps After Deployment

1. **Test API calls** from frontend
2. **Monitor logs** for errors
3. **Update frontend URL** in backend CORS if needed
4. **Set up auto-redeploy** on GitHub push (default)
5. **Configure domain** (optional - Render provides free .onrender.com)

---

## Important Notes

⚠️ **Before Production:**
- [ ] Replace SQLite with PostgreSQL for data persistence
- [ ] Configure proper authentication if needed
- [ ] Set up monitoring and alerting
- [ ] Configure custom domain (optional)
- [ ] Enable auto-redeploy on GitHub push
- [ ] Test database backups

⚠️ **Free Tier Limitations:**
- Services spin down after 15 min inactivity (cold start ~15 sec)
- Upgrade to Starter or higher for production use
- Shared CPU with other customers

---

## Support

- Render Docs: https://render.com/docs
- Render Dashboard: https://render.com/dashboard
- Community: https://render.com/community
