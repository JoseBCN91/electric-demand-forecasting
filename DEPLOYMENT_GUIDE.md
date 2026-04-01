# 🚀 HF Spaces Deployment - Step by Step

## Prerequisites Check

✅ Code committed to GitHub: `feature/nube-microservicios` branch  
✅ Dockerfile ready with health checks  
✅ All dependencies in requirements.txt  
⏳ ENTSOE_API_KEY ready

---

## Step 1: Create HF Space (NO CODE - Browser Only)

**Time: ~2 minutes**

1. **Open browser** → https://huggingface.co/new-space

2. **Fill form**:
   - Owner: `Your-HF-Username` (select your account)
   - Space name: `electric-demand-forecasting`
   - License: `MIT`
   - SDK: **`Docker`** (very important!)

3. **Click**: `Create space`

4. Wait for page to load (you'll see empty repo)

**✅ Space Created!**

---

## Step 2: Add Secret (API Key)

**Time: ~1 minute**

1. In your new Space, go to **Settings** tab (top right)

2. Scroll down to **Repository secrets**

3. Click **Add new secret**

4. Enter:
   - **Key**: `ENTSOE_API_KEY`
   - **Value**: [Paste your ENTSOE API key from transparency.entsoe.eu]

5. Click **Add secret**

**✅ Secret Added!**

---

## Step 3: Push Code to HF Spaces

**Time: ~2 minutes**

### Open PowerShell and Run These Commands:

```powershell
# Set your HF username (EDIT THIS!)
$HF_USERNAME = "your-huggingface-username"

# Create a deployment folder
$DEPLOY_DIR = "$env:TEMP\hf-spaces-deploy"
if (Test-Path $DEPLOY_DIR) { Remove-Item $DEPLOY_DIR -Recurse -Force }
New-Item -ItemType Directory -Path $DEPLOY_DIR | Out-Null
cd $DEPLOY_DIR

# Clone your new HF Space
git clone https://huggingface.co/spaces/$HF_USERNAME/electric-demand-forecasting .

# Add GitHub as remote (where your code is)
git remote add github https://github.com/JoseBCN91/electric-demand-forecasting.git

# Pull code from GitHub
git pull github feature/nube-microservicios

# Push to HF Spaces (this triggers the build!)
git push origin main
```

**⏳ Build Starting!**

You'll see output like:
```
Enumerating objects...
Counting objects...
Compressing objects...
Writing objects...
Total 100 (delta 50)
remote: Building your space...
```

---

## What Happens After Push

### 🏗️ Building Phase (2-5 minutes)

1. **Go to your Space**: https://huggingface.co/spaces/YOUR-USERNAME/electric-demand-forecasting

2. **Click**: **Logs** tab (top right)

3. **Watch** the Docker build:
   ```
   Step 1/20 : FROM python:3.11-slim
   Step 2/20 : WORKDIR /app
   ...
   Step 20/20 : RUN chmod +x run.sh
   SUCCESS: BuildKit build succeeded ✅
   ```

### 🚀 Startup Phase (1-2 minutes)

After build succeeds, you see:
```
🚀 Production Startup
🐍 Python version: Python 3.11.x
✅ Verifying essential packages...
📡 Starting FastAPI server on port 8000...
⏳ Waiting for API initialization (10 seconds)...
🏥 Checking API health...
✅ API is healthy!
📊 Starting Streamlit dashboard on port 7860...
```

### ✅ Ready! (10-30 seconds later)

- API accessible
- Streamlit dashboard running
- Metrics collecting

---

## Test Your Deployment

Once you see "API is healthy!" in logs:

### Get Your Space URL

Format: `https://YOUR-USERNAME-electric-demand-forecasting.hf.space`

### Test Health Check

```powershell
$URL = "https://your-username-electric-demand-forecasting.hf.space"

# Test health
curl "$URL/health"

# Should return:
# {"status": "healthy", "model_available": false}  ← Still training
# Then after 2 min:
# {"status": "healthy", "model_available": true}   ← Ready!
```

### Test Prediction Endpoint

```powershell
$URL = "https://your-username-electric-demand-forecasting.hf.space"
$payload = @{
    horizon = 24
    country = "ES"
    confidence_levels = @(80, 95)
} | ConvertTo-Json

curl -X POST "$URL/predict" `
  -H "Content-Type: application/json" `
  -d $payload
```

**Expected response** (success):
```json
{
  "request_id": "abc123-def456",
  "country": "ES",
  "forecast": [
    {"hour": 1, "point_forecast": 32500, "forecast_80": 31200, "forecast_95": 29800},
    ...
  ],
  "model_available": true,
  "latency_ms": 145
}
```

### View Metrics

```powershell
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

## Your Live URLs

| What | URL |
|------|-----|
| **Dashboard** | `https://YOUR-USERNAME-electric-demand-forecasting.hf.space/` |
| **API Docs** | `https://YOUR-USERNAME-electric-demand-forecasting.hf.space/docs` |
| **Health** | `https://YOUR-USERNAME-electric-demand-forecasting.hf.space/health` |
| **Metrics** | `https://YOUR-USERNAME-electric-demand-forecasting.hf.space/metrics` |
| **Logs** | `https://huggingface.co/spaces/YOUR-USERNAME/electric-demand-forecasting/logs` |

---

## Troubleshooting

### Build fails with "ENTSOE_API_KEY not found"
- ✅ Go to Space Settings → Repository secrets
- ✅ Verify `ENTSOE_API_KEY` is listed
- ✅ Restart build by going to Building tab and clicking "Build from main"

### API returns 502 on first request
- ✅ **This is expected!** Model is training (takes 1-2 minutes)
- ✅ Check Logs for "Training completed"
- ✅ Wait 2-3 minutes, then retry

### "Connection refused" error
- ✅ Reload browser (clear cache: Ctrl+Shift+Del)
- ✅ Check Logs for errors
- ✅ Wait 30 seconds and try again

### Docker build stuck on "Installing Python packages"
- ✅ This is normal (can take 2-3 minutes)
- ✅ Just wait, it's downloading 50+ packages
- ✅ Check Logs to see progress

---

## Monitor Your Space

### Real-Time Logs
- Go to Space → **Logs** tab
- Auto-refreshes every 5 seconds
- Shows all API requests and errors

### Metrics Endpoint
```powershell
# Check API health every 30 seconds
while ($true) {
    curl https://your-username-electric-demand-forecasting.hf.space/metrics | ConvertFrom-Json | Select health_status, success_rate, avg_latency_ms
    Start-Sleep -Seconds 30
}
```

---

## Next Steps

1. ✅ Create HF Space (Step 1)
2. ✅ Add ENTSOE_API_KEY (Step 2)
3. ⏳ **Run PowerShell commands** (Step 3)
4. ⏳ Watch build in Logs
5. ⏳ Test endpoints with curl
6. ✅ Share URL with team!

---

## Success Indicators

When you see these messages in Logs, you're done:
- ✅ "BuildKit build succeeded"
- ✅ "API is healthy!"
- ✅ "Streamlit dashboard on port 7860"

And `/health` returns:
```json
{"status": "healthy", "model_available": true}
```

---

## Need More Help?

- **Full Guide**: [DEPLOY_HF_SPACES.md](../DEPLOY_HF_SPACES.md)
- **API Usage**: [README.md](../README.md)
- **Quick Ref**: [HF_DEPLOYMENT_QUICKSTART.md](../HF_DEPLOYMENT_QUICKSTART.md)

---

**Ready? Go to Step 1 and create that HF Space!** 🚀
