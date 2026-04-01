# Deploy to HF Spaces - Automated Script
# Run this to deploy your code to Hugging Face Spaces

param(
    [string]$HFUsername = "Jose91-BCN",
    [string]$SpaceName = "Electricity_demand"
)

Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Deploy to Hugging Face Spaces              ║" -ForegroundColor Cyan
Write-Host "║     GitHub → HF Space                          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Configuration
$HFSpaceURL = "https://huggingface.co/spaces/$HFUsername/$SpaceName"
$HFRepoURL = "https://huggingface.co/spaces/$HFUsername/$SpaceName"
$GitHubRepo = "https://github.com/JoseBCN91/electric-demand-forecasting.git"
$GitHubBranch = "feature/nube-microservicios"

Write-Host "Configuration:" -ForegroundColor Green
Write-Host "  HF Username: $HFUsername"
Write-Host "  Space Name: $SpaceName"
Write-Host "  GitHub Repo: $GitHubRepo"
Write-Host "  GitHub Branch: $GitHubBranch"
Write-Host ""

# Step 1: Verify prerequisites
Write-Host "Step 1: Checking prerequisites..." -ForegroundColor Yellow
Write-Host ""

# Check git
try {
    $gitVersion = git --version 2>&1
    Write-Host "✅ Git installed: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git not found. Please install Git from https://git-scm.com/" -ForegroundColor Red
    exit 1
}

# Check curl
try {
    $curlVersion = curl --version 2>&1 | Select-Object -First 1
    Write-Host "✅ Curl available: $curlVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Curl not found (optional, can use PowerShell)" -ForegroundColor Yellow
}

# Step 2: Manual HF configuration reminder
Write-Host ""
Write-Host "Step 2: HF Space Configuration" -ForegroundColor Yellow
Write-Host ""
Write-Host "❗ Before proceeding, please ensure you have:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Added ENTSOE_API_KEY secret:"
Write-Host "     → Go to: $HFSpaceURL/settings"
Write-Host "     → Repository secrets → Add new secret"
Write-Host "     → Key: ENTSOE_API_KEY"
Write-Host "     → Value: [Your ENTSOE API key]"
Write-Host ""
Write-Host "  2. HF Space exists and is ready"
Write-Host ""

$ready = Read-Host "Have you added the ENTSOE_API_KEY secret? (y/n)"
if ($ready -ne "y" -and $ready -ne "Y") {
    Write-Host "⏸️  Skipping deployment. Please add the secret first." -ForegroundColor Yellow
    Write-Host "   Go to: $HFSpaceURL/settings" -ForegroundColor Cyan
    exit 0
}

# Step 3: Create deployment directory
Write-Host ""
Write-Host "Step 3: Setting up deployment directory..." -ForegroundColor Yellow

$deployDir = "$env:TEMP\hf-spaces-deploy-$(Get-Random)"
Write-Host "Deployment directory: $deployDir"

if (Test-Path $deployDir) {
    Remove-Item $deployDir -Recurse -Force | Out-Null
}

New-Item -ItemType Directory -Path $deployDir | Out-Null
cd $deployDir
Write-Host "✅ Deployment directory created" -ForegroundColor Green

# Step 4: Clone HF Space
Write-Host ""
Write-Host "Step 4: Cloning HF Space repository..." -ForegroundColor Yellow

try {
    git clone $HFRepoURL . 2>&1 | Out-Null
    Write-Host "✅ HF Space cloned successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to clone HF Space" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Check:" -ForegroundColor Yellow
    Write-Host "   - Space URL is correct: $HFRepoURL"
    Write-Host "   - You have access to $HFSpaceURL"
    Write-Host "   - Internet connection is working"
    exit 1
}

# Step 5: Add GitHub remote
Write-Host ""
Write-Host "Step 5: Configuring GitHub remote..." -ForegroundColor Yellow

try {
    git remote add github $GitHubRepo 2>&1 | Out-Null
    Write-Host "✅ GitHub remote added" -ForegroundColor Green
} catch {
    Write-Host "⚠️  GitHub remote may already exist (OK)" -ForegroundColor Yellow
}

# Step 6: Fetch from GitHub
Write-Host ""
Write-Host "Step 6: Fetching code from GitHub..." -ForegroundColor Yellow

try {
    git fetch github $GitHubBranch 2>&1 | Out-Null
    Write-Host "✅ Code fetched from GitHub" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to fetch from GitHub" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}

# Step 7: Merge code
Write-Host ""
Write-Host "Step 7: Merging code into HF Space..." -ForegroundColor Yellow

try {
    git merge github/$GitHubBranch --allow-unrelated-histories 2>&1 | Out-Null
    Write-Host "✅ Code merged successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Merge conflict or error" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Try manually:" -ForegroundColor Yellow
    Write-Host "   git checkout github/$GitHubBranch -- ."
    exit 1
}

# Step 8: Push to HF Spaces
Write-Host ""
Write-Host "Step 8: Pushing to HF Spaces (THIS STARTS THE BUILD!)..." -ForegroundColor Yellow
Write-Host ""

try {
    $output = git push origin main 2>&1
    Write-Host $output
    Write-Host "✅ Code pushed to HF Spaces!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to push to HF Spaces" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}

# Step 9: Success message
Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║             🎉 DEPLOYMENT STARTED!            ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "Your HF Space is now building!" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏱️  Expected timeline:" -ForegroundColor Yellow
Write-Host "   - Docker build: 2-5 minutes"
Write-Host "   - Model training (first run): 1-2 minutes"
Write-Host "   - Total: 3-7 minutes"
Write-Host ""

Write-Host "📊 Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  Watch the build in real-time:"
Write-Host "   → $HFSpaceURL/logs"
Write-Host ""
Write-Host "2️⃣  Look for these success messages:"
Write-Host "   ✅ 'BuildKit build succeeded'"
Write-Host "   ✅ 'API is healthy!'"
Write-Host "   ✅ 'Streamlit dashboard on port 7860'"
Write-Host ""
Write-Host "3️⃣  Once ready, test your API:"
Write-Host ""
Write-Host "   Health check:"
Write-Host "   curl $HFSpaceURL/health"
Write-Host ""
Write-Host "   Make prediction:"
Write-Host "   curl -X POST $HFSpaceURL/predict \"
Write-Host "     -H 'Content-Type: application/json' \"
Write-Host "     -d '{\"horizon\": 24, \"country\": \"ES\"}'"
Write-Host ""
Write-Host "   View metrics:"
Write-Host "   curl $HFSpaceURL/metrics"
Write-Host ""

Write-Host "4️⃣  View your live space:"
Write-Host "   → $HFSpaceURL"
Write-Host ""

# Cleanup
Write-Host "🧹 Cleaning up temporary directory..." -ForegroundColor Gray
cd /
Remove-Item $deployDir -Recurse -Force 2>&1 | Out-Null
Write-Host "✅ Cleanup complete" -ForegroundColor Green

Write-Host ""
Write-Host "Happy deploying! 🚀" -ForegroundColor Green
Write-Host ""
