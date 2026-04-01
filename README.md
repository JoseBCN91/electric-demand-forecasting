---
title: Electric Demand Forecasting
emoji: ⚡
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# ⚡ Electric Demand Forecasting

A production-ready **European electricity demand forecasting system** using time-series models (CatBoost + MLForecast) with real-time API, monitoring, and Hugging Face Spaces deployment.

## 🎯 Quick Start

### Local Development

```bash
# 1. Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your ENTSOE_API_KEY

# 3. Run the production stack
./run.sh  # API + Dashboard
```

**API**: http://localhost:8000 (FastAPI)  
**Dashboard**: http://localhost:7860 (Streamlit)  
**API Docs**: http://localhost:8000/docs (OpenAPI)

---

## 📡 API Endpoints

### Predict Electricity Demand

**POST** `/predict`

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "horizon": 24,
    "country": "ES",
    "confidence_levels": [80, 95]
  }'
```

**Request Parameters:**
- `horizon` (int): Hours to forecast [1-168] (default: 24)
- `country` (str): Country code: ES/FR/DE/IT (default: ES)
- `confidence_levels` (list): Percentiles [1-99] (default: [80, 95])

**Response Example:**
```json
{
  "request_id": "abc123-def456",
  "country": "ES",
  "horizon": 24,
  "forecast": [
    {
      "hour": 1,
      "point_forecast": 32500,
      "forecast_80": 31200,
      "forecast_95": 29800
    },
    { "hour": 2, "point_forecast": 30800, "forecast_80": 29500, "forecast_95": 28100 }
  ],
  "timestamp": "2026-04-01T10:30:00",
  "model_available": true,
  "latency_ms": 145
}
```

**Error Responses:**
```bash
# Invalid horizon
curl -X POST http://localhost:8000/predict \
  -d '{"horizon": 500, "country": "ES"}'
# → 422: "horizon must be between 1 and 168 hours"

# Invalid country
curl -X POST http://localhost:8000/predict \
  -d '{"horizon": 24, "country": "XX"}'
# → 422: "country must be one of: ES, FR, DE, IT"

# If weather API fails (graceful degradation)
# → 502: "Unable to fetch weather data. Using default values."
```

### API Health

**GET** `/health`

```bash
curl http://localhost:8000/health
# → {"status": "healthy", "model_available": true}
```

### Monitoring & Metrics

**GET** `/metrics`

```bash
curl http://localhost:8000/metrics
```

**Response:**
```json
{
  "total_requests": 234,
  "success_rate": 0.985,
  "avg_latency_ms": 142,
  "cache_hit_rate": 0.72,
  "errors_by_type": {
    "WeatherAPIError": 2,
    "InvalidInput": 1
  },
  "health_status": "healthy",
  "uptime_hours": 4.5
}
```

### API Documentation

**GET** `/docs` (Swagger/OpenAPI)  
**GET** `/redoc` (ReDoc)

---

## 🔧 Configuration

### Environment Variables

Create `.env` file (see [.env.example](.env.example)):

```bash
# Required for data ingestion
ENTSOE_API_KEY=your_entsoe_api_key

# Optional: Google Cloud Storage (falls back to local)
GCP_CREDENTIALS_JSON=/path/to/credentials.json
MODEL_BUCKET_NAME=your-bucket-name

# Optional: API configuration (uses defaults from config.py)
API_RATE_LIMIT_PER_MINUTE=20  # Requests per minute
API_CACHE_TTL_MINUTES=30      # Weather cache duration
MODEL_MAX_AGE_DAYS=7          # Retrain if older

# Logging
LOG_LEVEL=INFO
```

### Get ENTSOE API Key

1. Visit [https://transparency.entsoe.eu/](https://transparency.entsoe.eu/)
2. Register for a free account
3. Request API access in your dashboard
4. Copy your API token to `ENTSOE_API_KEY`

### Google Cloud Storage (Optional)

If you want to store models in GCS:

```bash
# Create credentials JSON
gcloud auth application-default create
# Set variables
export GCP_CREDENTIALS_JSON=$(cat ~/.config/gcloud/application_default_credentials.json)
export MODEL_BUCKET_NAME="your-bucket-name"
```

If not configured, models are stored locally in `/models/`.

---

## 🚀 Data Pipeline

### Run Complete ML Pipeline

```bash
# Requires ENTSOE_API_KEY in .env or environment
python data/scripts/run_pipeline.py
```

**Pipeline Steps:**
1. **Ingest**: Download 24-month load + weather data
2. **Process**: Clean, resample to hourly, handle missing values
3. **Train**: Build CatBoost model with lag features & confidence intervals

**Output:**
- `data/processed/features.parquet` - Raw features
- `data/processed/features_clean.parquet` - Cleaned dataset
- `models/model_prod.pkl` - Trained CatBoost model

### Lazy Training

The API automatically retrains the model if:
- Model is missing
- Model is older than 7 days
- Request triggers training and succeeds

---

## 📊 Monitoring & Logging

### JSON Structured Logging

All modules output JSON logs (one per line) with:
- Timestamp (ISO 8601)
- Log level (INFO, ERROR, WARNING)
- Logger name (api, model, data, training)
- Message + optional request_id, latency_ms

Example:
```json
{"timestamp": "2026-04-01T10:30:00.123456", "level": "INFO", "logger": "api", "message": "Prediction generated for ES", "request_id": "abc123", "latency_ms": 145}
```

### View Real-Time Metrics

```bash
# Container logs
docker logs -f electric-demand-forecasting

# API metrics endpoint
curl http://localhost:8000/metrics | jq .
```

---

## 🐳 Docker Deployment

### Build & Run Locally

```bash
# Build image
docker build -t electric-demand-forecasting:latest .

# Run container
docker run -p 8000:8000 -p 7860:7860 \
  -e ENTSOE_API_KEY=your_key \
  electric-demand-forecasting:latest
```

### Health Check

The container automatically checks `/health` endpoint:
```bash
docker inspect electric-demand-forecasting | grep -A 10 '"Health"'
```

---

## 🤗 Hugging Face Spaces Deployment

### Step-by-Step Setup

1. **Create Space**
   - Visit [https://huggingface.co/new-space](https://huggingface.co/new-space)
   - Select "Docker" as runtime
   - Name: `electric-demand-forecasting`

2. **Configure Secrets** (Settings → Repository Secrets)
   - `ENTSOE_API_KEY`: Your API key from ENTSOE
   - `GCP_CREDENTIALS_JSON`: (optional) GCS credentials
   - `MODEL_BUCKET_NAME`: (optional) GCS bucket name

3. **Connect Repository**
   ```bash
   git clone https://huggingface.co/spaces/your-username/electric-demand-forecasting
   cd electric-demand-forecasting
   git remote add github https://github.com/your-repo.git
   git pull github main
   git push
   ```

4. **Verify Deployment**
   - Logs appear in HF UI
   - API accessible at `https://your-username-electric-demand-forecasting.hf.space/`
   - Dashboard at `/` endpoint

### Expected Startup Time

- Cold start: 45-60 seconds (first model training)
- Warm start: 10-15 seconds (subsequent requests)
- Model lazy retrains on first request if >7 days old

---

## 🧪 Testing

### Run Test Suite

```bash
# Unit + Integration tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_validation.py -v
```

**Test Coverage:**
- Config validation: 9 tests
- API input validation: 11 tests
- Endpoint functionality: 9+ tests
- Total: 30+ tests

---

## 🐛 Troubleshooting

### API won't start
```json
{"level": "ERROR", "message": "Failed to load model"}
```
**Solutions:**
- Run `python data/scripts/run_pipeline.py` to train model
- Check `/models/` directory exists
- Verify `model_prod.pkl` present or use lazy training on first request

### Weather API failing
```
502: "Unable to fetch weather data. Using default values."
```
**Solutions:**
- API gracefully degrades; returns zeros for weather features (safe degradation)
- Check internet connection
- Open-Meteo API status: [status.open-meteo.com](https://status.open-meteo.com)

### ENTSOE rate limited
```json
{"level": "ERROR", "message": "ENTSOE: 429 Too Many Requests"}
```
**Solutions:**
- Wait before retrying (exponential backoff recommended)
- Check API key is valid: [transparency.entsoe.eu](https://transparency.entsoe.eu/)
- Verify IP whitelisted if required by ENTSOE

### Streamlit connection refused
```
StreamlitAPIException: Connection refused to localhost:7860
```
**Solutions:**
- Check port 7860 not in use: `lsof -i :7860`
- Increase sleep time in `run.sh` (change `sleep 5` to `sleep 10`)
- Ensure API health check passes before Streamlit starts

---

## 📚 Architecture

```
┌──────────────────────────────────────┐
│    Client (Browser / API)             │
└────────────────┬─────────────────────┘
                 │
        ┌────────┴─────────┐
        │                  │
    ┌───▼─────────┐   ┌───▼──────────┐
    │  FastAPI    │   │  Streamlit   │
    │  :8000      │   │  :7860       │
    │ (REST API)  │   │ (Dashboard)  │
    └───┬─────────┘   └──────────────┘
        │
    ┌───▼──────────────────────┐
    │   Prediction Pipeline     │
    │  1. Fetch Weather (TTL)   │
    │  2. Merge Historical      │
    │  3. Generate Forecast     │
    │  4. Record Metrics        │
    └───┬──────────────────────┘
        │
    ┌───▼──────────────────┐
    │  CatBoost Model      │
    │  (Lazy Retrain >7d)  │
    └──────────────────────┘
```

---

## 📦 Technology Stack

| Component | Tool | Version |
|-----------|------|---------|
| API | FastAPI | 0.109.0 |
| Model | CatBoost | 1.2.2 |
| Time Series | MLForecast | 0.11.3 |
| Validation | Pydantic | 2.6.0 |
| Dashboard | Streamlit | 1.30.0 |
| Runtime | Python | 3.11 |
| Configuration | YAML, dotenv | - |
| Logging | JSON | - |

---

## 📈 Performance

**Response Latency:**
- Cached weather: 80-120ms
- Fresh weather: 200-300ms (includes API call)
- Model generation: 50-100ms
- **Total: 80-300ms per request**

**Scalability:**
- 1 vCPU: ~30-50 req/sec
- For HF Spaces (<100 req/day): No scaling needed
- In-memory caching: Weather, metrics, request tracking

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing`
3. Write tests for your changes
4. Run `pytest tests/ -v`
5. Submit pull request

---

**Built with ❤️ for European electricity demand forecasting**
