# 🚀 Deploy to Hugging Face Spaces - Final Steps

**Your GitHub repo is ready!** Now deploy to HF Spaces in **3 steps** (5 minutes).

---

## Step 1: Create HF Space (2 minutes)

1. **Go to**: https://huggingface.co/new-space
   
2. **Fill in these fields**:
   - **Owner**: Select your account
   - **Space name**: `electric-demand-forecasting`
   - **License**: MIT
   - **SDK**: `Docker` ← **Important!**

3. **Click**: Create space

You'll see an empty repo. Don't worry—we'll add code in Step 3.

---

## Step 2: Add Your Secret (1 minute)

**This is required for the data pipeline to work.**

1. **Go to**: Your Space → **Settings** tab
2. **Scroll to**: Repository secrets
3. **Click**: Add new secret
4. **Enter**:
   - **Key**: `ENTSOE_API_KEY`
   - **Value**: [Paste your ENTSOE token]
5. **Click**: Add secret

**Done!** The API will use this automatically.

---

## Step 3: Push Code to HF Spaces (2 minutes)

### Open Terminal and Run These Commands:

```bash
# 1. Clone your new HF Space
git clone https://huggingface.co/spaces/YOUR-USERNAME/electric-demand-forecasting

# 2. Enter directory
cd electric-demand-forecasting

# 3. Add your GitHub as remote
git remote add github https://github.com/JoseBCN91/electric-demand-forecasting.git

# 4. Pull code from GitHub
git pull github feature/nube-microservicios

# 5. Push to HF Spaces (starts build immediately)
git push origin main
```

**Replace** `YOUR-USERNAME` with your actual HF username.

---

## What Happens Next

### While Building (2-5 minutes)
- **Watch the logs** in your Space → **Logs** tab
- You'll see Docker pulling Python, installing dependencies, building
- Look for GREEN checkmark: `SUCCESS: BuildKit build succeeded`

### On First Request (1-2 minutes)
- API loads Python model
- Lazy training triggers (trains from historical data)
- Logs show: `Training completed: YYYY-MM-DD`

### Then (10-15 seconds)
- API is ready! ✅
- Dashboard loads
- All endpoints functional

---

## Test Your Deployment

Once the build succeeds, test these endpoints:

```bash
# 1. Health check (should be first thing to work)
curl https://YOUR-USERNAME-electric-demand-forecasting.hf.space/health

# Response:
# {"status": "healthy", "model_available": false}  ← Wait 2 min for model
# {"status": "healthy", "model_available": true}   ← Ready!

# 2. Make a prediction (after model_available = true)
curl -X POST https://YOUR-USERNAME-electric-demand-forecasting.hf.space/predict \
  -H "Content-Type: application/json" \
  -d '{
    "horizon": 24,
    "country": "ES",
    "confidence_levels": [80, 95]
  }'

# Response:
# {
#   "request_id": "abc123...",
#   "country": "ES",
#   "horizon": 24,
#   "forecast": [
#     {"hour": 1, "point_forecast": 32500, "forecast_80": 31200, "forecast_95": 29800},
#     {"hour": 2, "point_forecast": 30800, ...},
#     ...
#   ],
#   "timestamp": "2026-04-01T10:30:00",
#   "model_available": true,
#   "latency_ms": 145
# }

# 3. View metrics
curl https://YOUR-USERNAME-electric-demand-forecasting.hf.space/metrics

# 4. Open in browser
# https://YOUR-USERNAME-electric-demand-forecasting.hf.space/
# Shows Streamlit dashboard + API docs at /docs
```

---

## Your Live URLs

Once deployed:

| What | URL |
|------|-----|
| **Dashboard** | `https://YOUR-USERNAME-electric-demand-forecasting.hf.space/` |
| **API Base** | `https://YOUR-USERNAME-electric-demand-forecasting.hf.space` |
| **API Docs** | `https://YOUR-USERNAME-electric-demand-forecasting.hf.space/docs` |
| **Health Check** | `https://YOUR-USERNAME-electric-demand-forecasting.hf.space/health` |
| **Metrics** | `https://YOUR-USERNAME-electric-demand-forecasting.hf.space/metrics` |

Replace `YOUR-USERNAME` with your actual Hugging Face username.

---

## Detailed Docs (If Needed)

- **Full Deployment Guide**: [DEPLOY_HF_SPACES.md](DEPLOY_HF_SPACES.md)
- **Complete API Docs**: [README.md](README.md)
- **What Was Built**: [PHASE_6_COMPLETION.md](PHASE_6_COMPLETION.md)
- **Production Status**: [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md)
- **Quick Timeline**: [HF_DEPLOYMENT_QUICKSTART.md](HF_DEPLOYMENT_QUICKSTART.md)

---

## Troubleshooting (See logs first!)

**Build fails?**
- Check **Logs** → look for error message
- Most common: Secret not added (Step 2)
- Solution: Add ENTSOE_API_KEY secret, restart build

**API returns 502?**
- ✅ **This is normal on first request** (model training)
- 🔍 Check logs for "Training completed"
- ⏳ Wait 2 minutes, then retry

**Connection refused?**
- Reload browser (clear cache)
- Check logs for any errors
- Wait 30 seconds and retry

---

## Share Your Success! 🎉

Once live, you can share the URL:
```
https://your-username-electric-demand-forecasting.hf.space/
```

Anyone can:
- Make predictions via `/predict` endpoint
- View real-time metrics at `/metrics`
- Access Streamlit dashboard
- Review API docs at `/docs`

---

## Next: Monitor Your Space

1. **Check logs regularly**
   - Go to Space → Logs (auto-refreshes)
   - Look for error patterns

2. **Monitor API health**
   - Call `/metrics` endpoint
   - Check success_rate, latency_ms
   - Alert if success_rate < 95%

3. **Keep ENTSOE API key valid**
   - Key expires if unused >1 year
   - Renew at transparency.entsoe.eu if needed

---

## Got Questions?

- **Can I modify the code?** Yes! Push changes to GitHub, they auto-deploy to HF
- **Can I use my own model?** Yes! Replace model file, push to GitHub
- **Does it cost anything?** No! Free tier supports <100 req/day
- **Can I add authentication?** Yes! Modify main.py to add auth middleware

---

**Your electricity demand forecasting API is about to go live!** ✨

Next action: Run the git commands above to deploy.

---

**Need help?** Check [DEPLOY_HF_SPACES.md](DEPLOY_HF_SPACES.md) for detailed troubleshooting.
