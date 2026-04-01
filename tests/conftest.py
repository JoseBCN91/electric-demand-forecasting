"""
Test configuration and fixtures for the forecasting API.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch


@pytest.fixture
def sample_load_data():
    """Sample electricity load data for testing."""
    dates = pd.date_range('2025-01-01', periods=24, freq='h')
    return pd.DataFrame({
        'unique_id': ['ES'] * 24,
        'ds': dates,
        'y': [3000 + i*10 for i in range(24)],
        'temperature': [15 + i*0.5 for i in range(24)],
        'wind_speed': [10 + i*0.2 for i in range(24)],
        'solar_rad': [100 + i*5 for i in range(24)]
    })


@pytest.fixture
def sample_weather_data():
    """Sample weather forecast data for testing."""
    dates = pd.date_range('2025-01-01', periods=168, freq='h')
    return pd.DataFrame({
        'unique_id': ['ES']*168 + ['FR']*168 + ['DE']*168 + ['IT']*168,
        'ds': list(dates)*4,
        'temperature': [15 + i*0.1 for i in range(168)]*4,
        'wind_speed': [10 + i*0.05 for i in range(168)]*4,
        'solar_rad': [100 + i*2 for i in range(168)]*4
    })


@pytest.fixture
def mock_model():
    """Mock trained ML model for testing."""
    model = Mock()
    
    # Mock make_future_dataframe
    dates = pd.date_range('2025-01-01', periods=24, freq='h')
    future_df = pd.DataFrame({
        'unique_id': ['ES']*24,
        'ds': dates
    })
    model.make_future_dataframe = Mock(return_value=future_df)
    
    # Mock predict method
    forecast_df = pd.DataFrame({
        'unique_id': ['ES']*24,
        'ds': dates,
        'CatBoost': [3000 + i*15 for i in range(24)],
        'CatBoost-lo-95': [2900 + i*15 for i in range(24)],
        'CatBoost-hi-95': [3100 + i*15 for i in range(24)]
    })
    model.predict = Mock(return_value=forecast_df)
    
    return model


@pytest.fixture
def api_client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    
    return TestClient(app)


@pytest.fixture
def mock_requests_get(monkeypatch):
    """Mock requests.get for weather API calls."""
    def mock_get(url, **kwargs):
        mock_response = Mock()
        mock_response.json.return_value = {
            "hourly": {
                "time": pd.date_range('2025-01-01', periods=168, freq='h').strftime('%Y-%m-%dT%H:%M').tolist(),
                "temperature_2m": [15 + i*0.1 for i in range(168)],
                "wind_speed_10m": [10 + i*0.05 for i in range(168)],
                "direct_radiation": [100 + i*2 for i in range(168)]
            }
        }
        mock_response.raise_for_status = Mock()
        return mock_response
    
    monkeypatch.setattr("requests.get", mock_get)
    return mock_get
