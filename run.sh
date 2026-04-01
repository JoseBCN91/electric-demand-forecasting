#!/bin/bash

# Don't exit on error - let services run even if health check fails
# This allows the API to continue running even if health check times out

echo "================================"
echo "🚀 Production Startup"
echo "================================"

# Verify Python version
echo "🐍 Python version:"
python --version

# Verify critical modules
echo "✅ Verifying essential packages..."
python -c "import fastapi, pandas, catboost, mlforecast; print('All packages available')"

# ==========================================
# START FASTAPI (Background)
# ==========================================
echo ""
echo "📡 Starting FastAPI server on port 8000..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --log-level info &
API_PID=$!
echo "API running with PID: $API_PID"

# Wait longer for API to start and initialize
echo "⏳ Waiting for API initialization (20 seconds)..."
sleep 20

# Health check using Python (more reliable than curl in containers)
echo "🏥 Checking API health..."
python3 << 'PYTHON_HEALTH_CHECK'
import requests
import sys
import time

max_retries = 10
retry_delay = 2

for i in range(1, max_retries + 1):
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=3)
        if response.status_code in [200, 206]:
            data = response.json()
            print(f"✅ API is {data.get('status', 'unknown')}!")
            sys.exit(0)
        else:
            print(f"   Retry {i}/{max_retries}... (status: {response.status_code}, waiting {retry_delay}s)")
    except (requests.ConnectionError, requests.Timeout, requests.RequestException) as e:
        if i == max_retries:
            print(f"⚠️  API health check timed out after {max_retries} attempts (continuing anyway)")
            print(f"   API may still be initializing - check logs")
            sys.exit(0)  # Don't fail - let API continue
        print(f"   Retry {i}/{max_retries}... (waiting {retry_delay}s)")
    
    time.sleep(retry_delay)

sys.exit(0)  # Non-blocking - API continues even if health check fails
PYTHON_HEALTH_CHECK

# ==========================================
# START STREAMLIT DASHBOARD (Foreground)
# ==========================================
echo ""
echo "📊 Starting Streamlit dashboard on port 7860..."
echo "================================"

# Streamlit config for production
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_PORT=7860
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_LOGGER_LEVEL=info
export STREAMLIT_CLIENT_SHOWERRORDETAILS=false

# Run Streamlit in foreground (Docker will monitor this)
streamlit run src/app/dashboard.py

# Cleanup on exit
trap "kill $API_PID 2>/dev/null || true" EXIT