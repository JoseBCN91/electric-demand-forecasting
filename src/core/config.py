"""
API Configuration and Settings

Centralized configuration management for API behavior, limits, and defaults.
"""

import os
from typing import List, Dict


class APISettings:
    """API configuration with sensible defaults."""
    
    # ==========================================
    # Server Configuration
    # ==========================================
    APP_NAME: str = "Electric Demand Forecasting API"
    APP_VERSION: str = "3.2.0"
    API_DESCRIPTION: str = "Real-time electricity demand forecasting for European countries"
    
    # ==========================================
    # Prediction Constraints
    # ==========================================
    MIN_HORIZON: int = 1  # Minimum forecast hours
    MAX_HORIZON: int = 168  # Maximum forecast hours (1 week)
    DEFAULT_HORIZON: int = 24  # Default forecast horizon
    DEFAULT_CONFIDENCE_LEVELS: List[int] = [80, 95]  # Default confidence percentiles
    
    # ==========================================
    # Supported Countries
    # ==========================================
    SUPPORTED_COUNTRIES: Dict[str, Dict] = {
        'ES': {"lat": 40.4168, "lon": -3.7038, "name": "Spain"},
        'FR': {"lat": 48.8566, "lon": 2.3522, "name": "France"},
        'DE': {"lat": 52.5200, "lon": 13.4050, "name": "Germany"},
        'IT': {"lat": 41.9028, "lon": 12.4964, "name": "Italy"}
    }
    DEFAULT_COUNTRY: str = "ES"
    
    # ==========================================
    # Rate Limiting
    # ==========================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 20  # Requests per minute
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # ==========================================
    # Caching
    # ==========================================
    CACHE_ENABLED: bool = True
    WEATHER_CACHE_TTL_MINUTES: int = 30  # Weather cache validity
    PREDICTION_CACHE_TTL_MINUTES: int = 5  # Prediction cache validity
    
    # ==========================================
    # External APIs
    # ==========================================
    WEATHER_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    WEATHER_API_TIMEOUT_SECONDS: int = 30
    
    # ==========================================
    # Model Configuration
    # ==========================================
    MODEL_BUCKET_NAME: str = os.environ.get("MODEL_BUCKET_NAME", "")
    MODEL_MAX_AGE_DAYS: int = 7
    
    # ==========================================
    # Logging
    # ==========================================
    LOG_LEVEL: str = "INFO"


# Global settings instance
settings = APISettings()


def get_settings() -> APISettings:
    """Get global API settings."""
    return settings


def validate_horizon(hours: int) -> bool:
    """Validate forecast horizon is within acceptable range."""
    return settings.MIN_HORIZON <= hours <= settings.MAX_HORIZON


def validate_country(country_code: str) -> bool:
    """Validate country code is supported."""
    return country_code in settings.SUPPORTED_COUNTRIES


def validate_confidence_levels(levels: List[int]) -> bool:
    """Validate confidence levels are percentiles (1-99)."""
    if not levels:
        return False
    return all(1 <= level <= 99 for level in levels)
