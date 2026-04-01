import pandas as pd
import numpy as np
import requests
import warnings
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

from src.api.model_loader import load_production_model
from src.utils.logger import api_logger
from src.core.config import (
    settings, validate_horizon, validate_country, validate_confidence_levels
)
from src.core.metrics import get_metrics_collector, PredictionMetrics

# ==========================================
# CONFIGURATION
# ==========================================
warnings.filterwarnings("ignore", category=UserWarning)

# Weather cache: {hash(params): (data, timestamp)}
_weather_cache: Dict[str, tuple] = {}

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.API_DESCRIPTION,
    version=settings.APP_VERSION
)

# Load model at startup
model = load_production_model()
api_logger.info(f"API initialized. Model available: {model is not None}")


# ==========================================
# PYDANTIC MODELS
# ==========================================
class PredictRequest(BaseModel):
    """Request model for prediction endpoint with validation."""
    horizon: int = Field(default=settings.DEFAULT_HORIZON, ge=1, le=settings.MAX_HORIZON)
    country: str = Field(default=settings.DEFAULT_COUNTRY)
    levels: Optional[List[int]] = Field(default=settings.DEFAULT_CONFIDENCE_LEVELS)
    
    @validator('country')
    def validate_country_field(cls, v):
        if not validate_country(v):
            supported = ", ".join(settings.SUPPORTED_COUNTRIES.keys())
            raise ValueError(f"Unsupported country: {v}. Supported: {supported}")
        return v
    
    @validator('levels')
    def validate_levels_field(cls, v):
        if v and not validate_confidence_levels(v):
            raise ValueError("Confidence levels must be integers between 1 and 99")
        return v or settings.DEFAULT_CONFIDENCE_LEVELS


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    model_available: bool
    version: str


class ForecastData(BaseModel):
    """Individual forecast record."""
    timestamp: str
    demand_mw: float
    confidence_level: Optional[int] = None
    upper_bound: Optional[float] = None
    lower_bound: Optional[float] = None


class PredictResponse(BaseModel):
    """Response model for prediction endpoint."""
    status: str
    country: str
    horizon_hours: int
    forecast_timestamp: str
    data: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    """Response model for errors."""
    status: str
    error_message: str
    timestamp: str


# ==========================================
# UTILITY FUNCTIONS
# ==========================================
def _get_weather_cache_key(country_codes: List[str]) -> str:
    """Generate cache key for weather data."""
    return f"weather_{'_'.join(sorted(country_codes))}"


def _get_cached_weather(country_codes: List[str]) -> Optional[pd.DataFrame]:
    """Retrieve cached weather data if valid."""
    if not settings.CACHE_ENABLED:
        return None
    
    cache_key = _get_weather_cache_key(country_codes)
    if cache_key in _weather_cache:
        data, timestamp = _weather_cache[cache_key]
        age_minutes = (time.time() - timestamp) / 60
        if age_minutes < settings.WEATHER_CACHE_TTL_MINUTES:
            api_logger.debug(f"Weather cache hit (age: {age_minutes:.1f} min)")
            return data
        else:
            del _weather_cache[cache_key]
    
    return None


def _cache_weather(country_codes: List[str], data: pd.DataFrame):
    """Cache weather data with timestamp."""
    if not settings.CACHE_ENABLED:
        return
    
    cache_key = _get_weather_cache_key(country_codes)
    _weather_cache[cache_key] = (data, time.time())
    api_logger.debug(f"Weather data cached (key: {cache_key})")


def get_broad_weather_europe() -> pd.DataFrame:
    """
    Fetch weather forecast for all supported countries.
    Uses caching to minimize external API calls.
    """
    country_codes = list(settings.SUPPORTED_COUNTRIES.keys())
    
    # Try cache first
    cached_weather = _get_cached_weather(country_codes)
    if cached_weather is not None:
        return cached_weather
    
    api_logger.info(f"Fetching fresh weather for {len(country_codes)} countries")
    all_weather_dfs = []
    
    for country_code, coords_info in settings.SUPPORTED_COUNTRIES.items():
        try:
            params = {
                "latitude": coords_info["lat"],
                "longitude": coords_info["lon"],
                "past_days": 1,
                "forecast_days": 7,
                "hourly": ["temperature_2m", "wind_speed_10m", "direct_radiation"],
                "timezone": "UTC"
            }
            
            api_logger.debug(f"Fetching weather for {country_code}")
            response = requests.get(
                settings.WEATHER_API_URL,
                params=params,
                timeout=settings.WEATHER_API_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            data = response.json()["hourly"]
            
            df = pd.DataFrame({
                "unique_id": country_code,
                "ds": pd.to_datetime(data["time"]),
                "temperature": data["temperature_2m"],
                "wind_speed": data["wind_speed_10m"],
                "solar_rad": data["direct_radiation"]
            })
            
            df['ds'] = df['ds'].dt.tz_localize(None)
            all_weather_dfs.append(df)
            
        except requests.RequestException as e:
            api_logger.error(f"Failed to fetch weather for {country_code}: {str(e)}")
            raise HTTPException(
                status_code=502,
                detail=f"Weather service error for {country_code}: {str(e)}"
            )
    
    result = pd.concat(all_weather_dfs, ignore_index=True)
    _cache_weather(country_codes, result)
    return result


# ==========================================
# API ENDPOINTS
# ==========================================
@app.get("/health", response_model=HealthResponse)
def health_check():
    """
    Health check endpoint.
    Returns API status and model availability.
    """
    api_logger.debug("Health check requested")
    return {
        "status": "healthy" if model is not None else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "model_available": model is not None,
        "version": settings.APP_VERSION
    }


@app.get("/metrics")
def get_metrics(minutes: int = 60):
    """
    Get API metrics and performance statistics.
    
    Args:
        minutes: Time window for aggregated stats (default: 60 minutes)
        
    Returns:
        Aggregated metrics including success rate, latency, and cache performance
    """
    metrics_collector = get_metrics_collector()
    stats = metrics_collector.get_stats(minutes=minutes)
    health = metrics_collector.get_health_status()
    
    api_logger.debug(f"Metrics requested for {minutes}m window")
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "health": health,
        "statistics": stats,
        "top_errors": [
            {"error_type": err_type, "count": count}
            for err_type, count in metrics_collector.get_top_errors(5)
        ]
    }


@app.get("/")
def root():
    """Root endpoint with API information."""
    api_logger.debug("Root endpoint accessed")
    return {
        "status": "online",
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "predict": "/predict",
            "docs": "/docs"
        }
    }


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """
    Forecast electricity demand for a country.
    
    Returns hourly demand predictions with optional confidence intervals.
    """
    req_id = f"{int(time.time() * 1000)}"
    api_logger.info(f"[{req_id}] Prediction: {request.country}, horizon={request.horizon}h")
    start_time = time.time()
    metrics_collector = get_metrics_collector()
    cache_hit = False
    
    try:
        # Validate model availability
        if model is None:
            api_logger.warning(f"[{req_id}] Model not available - returning demo predictions")
            duration_ms = (time.time() - start_time) * 1000
            
            # Generate demo/sample predictions for demonstration
            demo_data = []
            base_demand = 32000 if request.country == "ES" else 28000 if request.country == "FR" else 35000 if request.country == "DE" else 27000
            
            from datetime import timedelta
            now = datetime.utcnow()
            for hour in range(1, request.horizon + 1):
                ts = (now + timedelta(hours=hour)).isoformat()
                # Simple sinusoidal pattern for demo
                variation = 5000 * (1 + 0.5 * np.sin(hour * 3.14159 / 12))
                point_forecast = base_demand + variation
                
                forecast_point = {
                    "timestamp": ts,
                    "demand_mw": round(point_forecast, 2),
                }
                
                # Add confidence intervals if requested
                for level in (request.levels or settings.DEFAULT_CONFIDENCE_LEVELS):
                    margin = (100 - level) / 100 * 3000
                    forecast_point[f"forecast_{level}"] = round(point_forecast - margin, 2)
                
                demo_data.append(forecast_point)
            
            metrics_collector.record(PredictionMetrics(
                request_id=req_id,
                country=request.country,
                horizon_hours=request.horizon,
                latency_ms=duration_ms,
                cache_hit=False,
                model_available=False,
                status="demo_mode",
                timestamp=datetime.utcnow(),
                error_message="Model not available - using demo data"
            ))
            
            return {
                "status": "demo",
                "country": request.country,
                "horizon_hours": request.horizon,
                "forecast_timestamp": datetime.utcnow().isoformat(),
                "data": demo_data,
                "message": "⚠️ Demo mode: Model not available. Train a model to get real predictions. See /docs for API details."
            }

        # Create template for future dates
        expected_df = model.make_future_dataframe(h=request.horizon)

        # Fetch weather data (with cache tracking)
        try:
            cached_before = len(_weather_cache)
            weather_df = get_broad_weather_europe()
            cache_hit = len(_weather_cache) > cached_before or cached_before > 0
        except HTTPException:
            raise
        except Exception as e:
            api_logger.error(f"[{req_id}] Weather fetch error: {str(e)}")
            raise HTTPException(status_code=502, detail=f"Weather service error: {str(e)}")

        # Merge and clean data
        X_df = pd.merge(expected_df, weather_df, on=['unique_id', 'ds'], how='left')
        X_df = X_df.sort_values(['unique_id', 'ds'])
        
        # Fill missing weather values
        cols_clima = ['temperature', 'wind_speed', 'solar_rad']
        X_df[cols_clima] = X_df.groupby('unique_id')[cols_clima].ffill().bfill()
        X_df[cols_clima] = X_df[cols_clima].fillna(0)

        # Generate predictions
        api_logger.debug(f"[{req_id}] Generating predictions")
        forecast = model.predict(
            h=request.horizon,
            level=request.levels,
            X_df=X_df
        )

        # Format response
        if isinstance(forecast, pd.DataFrame):
            forecast_filtered = forecast[forecast['unique_id'] == request.country].copy()
            
            if 'ds' in forecast_filtered.columns:
                forecast_filtered['ds'] = forecast_filtered['ds'].dt.strftime('%Y-%m-%dT%H:%M:%S')
            
            result = forecast_filtered.reset_index(drop=True).to_dict(orient="records")
        else:
            result = forecast.tolist()

        duration_ms = (time.time() - start_time) * 1000
        api_logger.info(f"[{req_id}] Success: {len(result)} forecasts in {duration_ms:.0f}ms")
        
        # Record success metrics
        metrics_collector.record(PredictionMetrics(
            request_id=req_id,
            country=request.country,
            horizon_hours=request.horizon,
            latency_ms=duration_ms,
            cache_hit=cache_hit,
            model_available=True,
            status="success",
            timestamp=datetime.utcnow(),
            confidence_min=min(request.levels) if request.levels else None,
            confidence_max=max(request.levels) if request.levels else None
        ))
        
        return {
            "status": "success",
            "country": request.country,
            "horizon_hours": request.horizon,
            "forecast_timestamp": datetime.utcnow().isoformat(),
            "data": result
        }

    except HTTPException as e:
        duration_ms = (time.time() - start_time) * 1000
        error_status = "api_error" if e.status_code >= 500 else "client_error"
        metrics_collector.record(PredictionMetrics(
            request_id=req_id,
            country=request.country,
            horizon_hours=request.horizon,
            latency_ms=duration_ms,
            cache_hit=cache_hit,
            model_available=model is not None,
            status=error_status,
            timestamp=datetime.utcnow(),
            error_message=e.detail
        ))
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        api_logger.error(f"[{req_id}] Error in {duration_ms:.0f}ms: {str(e)}", exc_info=True)
        metrics_collector.record(PredictionMetrics(
            request_id=req_id,
            country=request.country,
            horizon_hours=request.horizon,
            latency_ms=duration_ms,
            cache_hit=cache_hit,
            model_available=model is not None,
            status="internal_error",
            timestamp=datetime.utcnow(),
            error_message=str(e)
        ))
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


# ==========================================
# STARTUP/SHUTDOWN
# ==========================================
@app.on_event("startup")
async def startup_event():
    """Initialize API on startup."""
    separator = "="*70
    api_logger.info(separator)
    api_logger.info(f"API STARTUP: {settings.APP_NAME} v{settings.APP_VERSION}")
    api_logger.info(separator)
    if model is None:
        api_logger.warning("⚠️ Model not available. Predictions will fail.")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    api_logger.info(f"API shutdown: {settings.APP_NAME}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)