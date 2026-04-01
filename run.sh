#!/bin/bash

set -e  # Exit on error

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

# Wait for API to start
echo "⏳ Waiting for API initialization (10 seconds)..."
sleep 10

# Health check
echo "🏥 Checking API health..."
for i in {1..5}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is healthy!"
        break
    fi
    if [ $i -eq 5 ]; then
        echo "❌ API health check failed after 5 attempts"
        kill $API_PID 2>/dev/null || true
        exit 1
    fi
    echo "   Retry $i/5... (waiting 2 seconds)"
    sleep 2
done

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