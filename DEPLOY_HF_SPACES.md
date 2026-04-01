# 🚀 Deploy to Hugging Face Spaces

This guide walks you through deploying the Electric Demand Forecasting system to Hugging Face Spaces for **free**.

## ⚡ What You'll Get

- **Public API** at `https://your-username-electric-demand-forecasting.hf.space/`
- **Streamlit Dashboard** at same URL
- **OpenAPI Docs** at `/docs` endpoint
- **Real-time Health Checks** (automatic restarts on failure)
- **Cost**: Free tier with 50GB storage, 16GB RAM, 2 vCPUs

---

## 📋 Prerequisites

1. **GitHub Account** - Code repository (publicly accessible)
2. **Hugging Face Account** - Free at [huggingface.co](https://huggingface.co)
3. **ENTSOE API Key** - Get at [transparency.entsoe.eu](https://transparency.entsoe.eu/) (~24-48h approval)
4. **5 minutes** - To complete the setup

---

## 🔑 Step 1: Create ENTSOE API Key

### Get Your API Key

1. Visit [ENTSOE Transparency Platform](https://transparency.entsoe.eu/)
2. Click **Register** → create a free account
3. Verify email address
4. Log in and go to **User Settings**
5. Click **Web API token** area
6. Request token approval (takes 1-2 business days)
7. Once approved, copy your token

**Example token**: `11223344-5566-7788-99aa-bbccddeeff00`

---

## 🤗 Step 2: Create Hugging Face Space

### Create New Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Fill in:
   - **Owner**: Your account
   - **Space name**: `electric-demand-forecasting`
   - **License**: MIT
   - **SDK**: `Docker`
   - **Space hardware**: (select if you want GPU, optional)
3. Click **Create space**

You'll see an empty repository.

---

## 🔐 Step 3: Configure Secrets

### Add Environment Variables

Your Hugging Face Space needs sensitive variables stored as **secrets**.

1. Go to your Space's **Settings** tab
2. Scroll to **Repository secrets**
3. Click **Add new secret**

#### Add Secret 1: ENTSOE_API_KEY

- **Key**: `ENTSOE_API_KEY`
- **Value**: `[Paste your token from Step 1]`
- Click **Add secret**

#### Add Secret 2 (Optional): GCP_CREDENTIALS_JSON

If you want to store models in Google Cloud Storage:

- **Key**: `GCP_CREDENTIALS_JSON`
- **Value**: [Paste your GCP credentials JSON (full file content)]
- Click **Add secret**

#### Add Secret 3 (Optional): MODEL_BUCKET_NAME

If using GCP:

- **Key**: `MODEL_BUCKET_NAME`
- **Value**: `your-gcs-bucket-name`
- Click **Add secret**

---

## 📦 Step 4: Connect GitHub Repository

### Option A: Push from GitHub (Recommended)

```bash
# Clone your HF Space locally
git clone https://huggingface.co/spaces/your-username/electric-demand-forecasting
cd electric-demand-forecasting

# Add your GitHub repo as remote
git remote add github https://github.com/your-username/electric-demand-forecasting.git

# Fetch latest code from GitHub
git pull github main

# Push to HF Spaces (triggers deployment)
git push origin main
```

### Option B: Manual Upload

If you don't have GitHub yet:

1. Go to your Space's **Files** tab
2. Click **Add file** → Upload files
3. Upload:
   - `src/` (entire folder)
   - `data/` (empty folders OK)
   - `models/` (empty folder)
   - `deployment/`
   - `Dockerfile`
   - `run.sh`
   - `pyproject.toml`
   - `requirements.txt`
   - `README.md`

---

## ✅ Step 5: Verify Deployment

### Watch Build Logs

1. Go to **Logs** tab in your Space
2. Watch the Docker build process
3. Expected logs:
   ```
   Step 1/20 : FROM python:3.11-slim
   ...
   [+] Building 85.2s (13/13) FINISHED
   BuildKit build succeeded
   ```

### Check Application Status

**First run (5-10 minutes):**
- Model training triggers automatically
- Logs show: `Training completed: 2026-04-01T10:30:00`
- Status shows ▶️ (running)

**Subsequent runs (30-60 seconds):**
- Loads cached model
- API ready immediately

### Test the API

Once running, test your deployment:

```bash
# Get your Space URL
# Format: https://your-username-electric-demand-forecasting.hf.space

# Test prediction endpoint
curl -X POST https://your-username-electric-demand-forecasting.hf.space/predict \
  -H "Content-Type: application/json" \
  -d '{
    "horizon": 24,
    "country": "ES",
    "confidence_levels": [80, 95]
  }'

# You should get:
# {"request_id": "...", "country": "ES", "forecast": [...]}
```

### Access Dashboard

Open in browser:
```
https://your-username-electric-demand-forecasting.hf.space/
```

You'll see the Streamlit dashboard for visualizing forecasts.

---

## 📊 Monitor Your Deployment

### Real-Time Logs

```bash
# From your computer, watch HF Space logs
# (Go to Space → Logs tab in UI)
```

### Health Status

```bash
# Check API health
curl https://your-username-electric-demand-forecasting.hf.space/health

# Should return:
# {"status": "healthy", "model_available": true}
```

### Metrics Endpoint

```bash
# View current metrics
curl https://your-username-electric-demand-forecasting.hf.space/metrics

# Returns:
# {"total_requests": 123, "success_rate": 0.98, "avg_latency_ms": 145, ...}
```

---

## 🐛 Troubleshooting

### Build Fails: "ENTSOE_API_KEY not found"

**Problem**: ENTSOE_API_KEY secret not added to Space.

**Solution**:
1. Go to Space **Settings**
2. Scroll to **Repository secrets**
3. Ensure `ENTSOE_API_KEY` is listed
4. Go to **Logs** and click **Restart Space**

### API Returns 502: "Unable to fetch weather data"

**Problem**: Network connectivity issue or Open-Meteo API down.

**Solution**: API gracefully degrades. Check:
- [Open-Meteo status](https://status.open-meteo.com)
- HF Space internet connectivity (usually not an issue)
- Wait 5 minutes and retry

### Model Training Takes Too Long

**Problem**: First request takes 1-2 minutes (model training).

**Solution**:
- This is expected behavior
- Subsequent requests cached (30s startup time)
- Check **Logs** for training progress

### Dashboard Shows "Connection Refused"

**Problem**: Streamlit dashboard can't connect to API.

**Solution**:
1. Ensure API is running via `/health` endpoint
2. Refresh browser (clear cache)
3. Check **Logs** for any errors
4. Wait 30 seconds and retry

---

## 🔄 Update Deployment

### Pull Latest Changes from GitHub

```bash
cd electric-demand-forecasting
git pull github main
git push origin main
```

HF Spaces automatically redeploys on new commits. Expected build time: 2-5 minutes.

### Rollback to Previous Version

```bash
git log --oneline  # Find commit hash
git revert <commit-hash>
git push origin main
```

---

## 🛡️ Production Deployment Notes

### High Availability

For production use (>1000 req/day), consider:

1. **Use GCS for Model Storage**
   - Add `GCP_CREDENTIALS_JSON` and `MODEL_BUCKET_NAME` secrets
   - Models persist across Space restarts
   - Share model across multiple instances

2. **Monitor with `/metrics` Endpoint**
   - Check success rate, latency, error types
   - Alert if success_rate < 95%

3. **Set Up Cron Job for Daily Training** (Optional)
   ```bash
   # Add to Dockerfile or separate cron container
   0 0 * * * python data/scripts/run_pipeline.py
   ```

### Cost Optimization

- **Free tier**: Sufficient for <100 req/day (your use case) ✅
- **Paid tier**: $7/month for more resources (only if needed)
- **Bring-your-own storage**: Use GCS for model persistence

---

## 🎯 Next Steps

1. ✅ Created Space
2. ✅ Added ENTSOE_API_KEY secret
3. ✅ Pushed code to HF Spaces
4. ⏳ Wait for Docker build (5-15 minutes)
5. ⏳ Test API at `/health` endpoint
6. ⏳ View dashboard in browser

### Share Your Space

Once running, you can share the URL:
```
https://your-username-electric-demand-forecasting.hf.space/
```

---

## 📚 Additional Resources

- **HF Spaces Docs**: [huggingface.co/docs/hub/spaces](https://huggingface.co/docs/hub/spaces)
- **Docker Deployment**: [huggingface.co/docs/hub/spaces-docker](https://huggingface.co/docs/hub/spaces-docker)
- **API Documentation**: Open `/docs` endpoint (Swagger UI)

---

## 💬 Need Help?

- Check **Logs** tab in HF UI for error messages
- Review [README.md](README.md) for API usage
- Check [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) for technical details
- Open issue on GitHub repository

---

**Deployed! 🎉 Your electricity demand forecasting API is now live.**
