# 🚀 HF Spaces Deployment Checklist

**Status**: Ready for deployment ✅

## Pre-Deployment Steps (Run Locally)

### 1. Commit Production Code
```bash
cd c:\Users\josep\Documents\GitHub\electric-demand-forecasting

# Add all production files
git add .
git add --force DEPLOY_HF_SPACES.md PHASE_6_COMPLETION.md PRODUCTION_READINESS.md .env.example
git add src/core/
git add tests/

# Verify what will be committed
git status

# Commit with message
git commit -m "Production readiness: Phase 6 deployment + hardening + monitoring"

# (Optional) If on feature branch, push to GitHub first
git push origin feature/nube-microservicios
```

### 2. Verify No Secrets in Commit
```bash
# Check that .env is NOT committed
git log -n 1 --name-only | grep ".env"
# Should return nothing

# Check that mlflow.db is NOT committed
git log -n 1 --name-only | grep "mlflow.db"
# Should return nothing
```

---

## HF Spaces Deployment (5 minutes)

### Step 1: Create HF Space (2 minutes)
1. Go to https://huggingface.co/new-space
2. Fill in:
   - **Owner**: your-username
   - **Name**: `electric-demand-forecasting`
   - **License**: MIT
   - **SDK**: Docker
3. Click **Create Space**
4. You'll see an empty repository

### Step 2: Configure Secrets (1 minute)
1. Go to Space **Settings** → **Repository secrets**
2. Click **Add new secret**
3. **Key**: `ENTSOE_API_KEY`
4. **Value**: [Paste your ENTSOE token]
5. Click **Add secret**

### Step 3: Push Code from GitHub (2 minutes)
```bash
# In your local repo
git clone https://huggingface.co/spaces/YOUR-USERNAME/electric-demand-forecasting
cd electric-demand-forecasting

# Add your GitHub repo as remote
git remote add github https://github.com/your-username/electric-demand-forecasting.git

# Fetch latest code
git pull github feature/nube-microservicios

# Push to HF Spaces (triggers build)
git push origin main
```

### Step 4: Verify Deployment (1 minute)
1. Go to your Space **Logs** tab
2. Watch the Docker build (takes 2-5 minutes)
3. Look for: `SUCCESS: BuildKit build succeeded`
4. Then API startup messages

### Step 5: Test Endpoints
```bash
# Get your URL from HF UI
# Format: https://your-username-electric-demand-forecasting.hf.space

curl https://your-username-electric-demand-forecasting.hf.space/health
# Should return: {"status": "healthy", "model_available": true}

curl -X POST https://your-username-electric-demand-forecasting.hf.space/predict \
  -H "Content-Type: application/json" \
  -d '{"horizon": 24, "country": "ES", "confidence_levels": [80, 95]}'
# Should return forecast with request_id, forecast data, latency
```

---

## Troubleshooting During Deployment

### Build hangs or fails
- Check **Logs** tab in HF UI
- Most common: ENTSOE_API_KEY not set as secret
- **Fix**: Settings → Repository secrets → verify key exists

### API 502 error on first request
- Expected! Model is training (takes 1-2 minutes on cold start)
- Check logs for "Training completed"
- Retry after 2 minutes

### "Connection refused" on second request
- API may have restarted during training
- Reload browser, wait 10 seconds, try again

---

## What Happens Next

✅ **Cold Start** (1-2 minutes):
- Docker pulls Python 3.11 image
- Installs dependencies (50 packages)
- Starts FastAPI + Streamlit
- Lazy-loads model (trains from scratch)
- Returns ready status

✅ **Warm Start** (30-60 seconds):
- Loads cached model
- API immediately responsive

✅ **Steady State** (<300ms per request):
- Weather cached 30 minutes
- Metrics collected per request
- Logs in real-time

---

## Your Space URL (After Deployment)
```
https://your-username-electric-demand-forecasting.hf.space/
```

**Share this URL to:**
- Access the API programmatically
- View the Streamlit dashboard
- Browse OpenAPI docs at `/docs`

---

## Monitor Your Space

### Check Logs (Real-Time)
Go to Space → Logs tab (auto-refreshes)

### Check API Health
```bash
curl https://your-username-electric-demand-forecasting.hf.space/metrics
```

Returns:
```json
{
  "total_requests": 2,
  "success_rate": 1.0,
  "avg_latency_ms": 234,
  "cache_hit_rate": 0.5,
  "errors_by_type": {},
  "health_status": "healthy",
  "uptime_hours": 0.15
}
```

---

## Next Steps After Deployment

1. ✅ Test all 5 endpoints (/health, /predict, /metrics, /docs, /)
2. ✅ Verify metrics are collecting
3. ✅ Check logs for any errors
4. ✅ Share Space URL with team

---

## Support

- **Detailed Guide**: [DEPLOY_HF_SPACES.md](DEPLOY_HF_SPACES.md)
- **API Docs**: [README.md](README.md)
- **Production Notes**: [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md)

---

**Ready to deploy? Follow the steps above!** 🚀
