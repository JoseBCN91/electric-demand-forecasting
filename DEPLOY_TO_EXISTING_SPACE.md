# ✅ Deploy to Existing HF Space

**Your HF Space**: https://huggingface.co/spaces/Jose91-BCN/Electricity_demand

**Username**: Jose91-BCN  
**Space Name**: Electricity_demand

---

## Step 1: Add Secret to Your Space (1 minute)

### Go to Space Settings

1. **Open**: https://huggingface.co/spaces/Jose91-BCN/Electricity_demand

2. **Click**: **Settings** (top menu)

3. **Find**: Repository secrets

4. **Click**: Add new secret

5. **Enter**:
   - **Key**: `ENTSOE_API_KEY`
   - **Value**: [Your ENTSOE API key]

6. **Click**: Add secret

✅ **Done! Secret added.**

---

## Step 2: Clone Space & Push Code (2 minutes)

### Run These PowerShell Commands:

```powershell
# Create a temporary directory for deployment
$DEPLOY_DIR = "$env:TEMP\hf-spaces-deploy"
if (Test-Path $DEPLOY_DIR) { Remove-Item $DEPLOY_DIR -Recurse -Force }
New-Item -ItemType Directory -Path $DEPLOY_DIR | Out-Null
cd $DEPLOY_DIR

echo "Step 1: Cloning HF Space..."
git clone https://huggingface.co/spaces/Jose91-BCN/Electricity_demand .

echo "Step 2: Adding GitHub as remote..."
git remote add github https://github.com/JoseBCN91/electric-demand-forecasting.git

echo "Step 3: Pulling code from GitHub..."
git pull github feature/nube-microservicios

echo "Step 4: Pushing to HF Space (this starts the build)..."
git push origin main

echo "Deployment started!"
```

### What You'll See

After running `git push`, you should see:
```
Enumerating objects: 100, done.
Counting objects: 100%
Compressing objects: 100%
Writing objects: 100%
total 100
remote: Building your space...
```

---

## Step 3: Watch the Build

1. **Go to**: https://huggingface.co/spaces/Jose91-BCN/Electricity_demand

2. **Click**: **Logs** tab (or **Building** tab)

3. **Watch** for:
   - Docker pulling Python 3.11 image
   - Installing 50+ packages (may take 2-3 minutes)
   - `SUCCESS: BuildKit build succeeded` ✅
   - API startup messages

---

## Step 4: Test Your Deployment

Once build completes and API is healthy:

```powershell
$URL = "https://Jose91-BCN-Electricity-demand.hf.space"

# Test health
echo "Testing health endpoint..."
curl "$URL/health"

# Should return: {"status": "healthy", "model_available": false if training}
# Or: {"status": "healthy", "model_available": true if ready}

# Test prediction (after model_available = true)
echo "Testing prediction endpoint..."
$payload = @{
    horizon = 24
    country = "ES"
    confidence_levels = @(80, 95)
} | ConvertTo-Json

curl -X POST "$URL/predict" `
  -H "Content-Type: application/json" `
  -d $payload

# View metrics
echo "Checking metrics..."
curl "$URL/metrics"
```

---

## Your Live Endpoints

Once deployed:

| Endpoint | URL |
|----------|-----|
| Dashboard | https://Jose91-BCN-Electricity-demand.hf.space/ |
| API Health | https://Jose91-BCN-Electricity-demand.hf.space/health |
| Predict | https://Jose91-BCN-Electricity-demand.hf.space/predict |
| Metrics | https://Jose91-BCN-Electricity-demand.hf.space/metrics |
| API Docs | https://Jose91-BCN-Electricity-demand.hf.space/docs |
| Logs | https://huggingface.co/spaces/Jose91-BCN/Electricity_demand/logs |

---

## Expected Timeline

- **Building**: 2-5 minutes (Docker build + dependency install)
- **Startup**: 1-2 minutes (first run triggers model training)
- **Ready**: 3-7 minutes total

### On First Request
- Model trains from scratch (~2 minutes)
- API returns 502 temporarily
- Check logs for "Training completed"
- Then API is ready!

### Subsequent Requests
- Model cached
- Response time: 80-300ms
- No more delays

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Build fails immediately** | Check if ENTSOE_API_KEY secret was added |
| **API returns 502** | Normal on first request (model training). Wait 2 min. |
| **Logs show error** | Go to Logs → Find error line → Check documentation |
| **Can't access /health** | Build still running. Check Logs tab. |
| **Models are already there?** | It pulls code from GitHub—our new code includes everything |

---

## Ready?

**Next Step**: Execute the PowerShell commands above to push code to your HF Space.

**Then**: Watch the build in the Logs tab.

**Finally**: Test the endpoints when build completes.

---

## Need Help?

- **Full Deployment Guide**: [DEPLOY_HF_SPACES.md](../DEPLOY_HF_SPACES.md)
- **Troubleshooting**: [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md#troubleshooting)
- **API Documentation**: [README.md](../README.md)

---

**Happy deploying!** 🚀
