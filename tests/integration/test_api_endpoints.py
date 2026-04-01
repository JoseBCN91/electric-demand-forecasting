"""
Integration tests for API endpoints.
"""

import pytest
from unittest.mock import patch, Mock
from src.api.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "model_available" in data
        assert "version" in data
    
    def test_health_check_structure(self, client):
        """Test health check response structure."""
        response = client.get("/health")
        data = response.json()
        
        assert data["status"] in ["healthy", "degraded"]
        assert data["model_available"] in [True, False]
        assert isinstance(data["version"], str)


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "online"
        assert "endpoints" in data
        assert "/health" in data["endpoints"].values()
        assert "/predict" in data["endpoints"].values()


class TestPredictEndpoint:
    """Test prediction endpoint with mocked model."""
    
    @patch('src.api.main.model')
    @patch('src.api.main.get_broad_weather_europe')
    def test_predict_valid_request(self, mock_weather, mock_model, client):
        """Test valid prediction request."""
        import pandas as pd
        
        # Mock weather data
        dates = pd.date_range('2025-01-01', periods=168, freq='h')
        mock_weather.return_value = pd.DataFrame({
            'unique_id': ['ES']*168 + ['FR']*168 + ['DE']*168 + ['IT']*168,
            'ds': list(dates)*4,
            'temperature': [15]*672,
            'wind_speed': [10]*672,
            'solar_rad': [100]*672
        })
        
        # Mock model
        mock_model.make_future_dataframe.return_value = pd.DataFrame({
            'unique_id': ['ES']*24,
            'ds': pd.date_range('2025-01-01', periods=24, freq='h')
        })
        
        forecast_df = pd.DataFrame({
            'unique_id': ['ES']*24,
            'ds': pd.date_range('2025-01-01', periods=24, freq='h'),
            'CatBoost': [3000]*24,
            'CatBoost-lo-95': [2900]*24,
            'CatBoost-hi-95': [3100]*24
        })
        mock_model.predict.return_value = forecast_df
        
        # Make request
        response = client.post("/predict", json={
            "horizon": 24,
            "country": "ES",
            "levels": [80, 95]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["country"] == "ES"
        assert data["horizon_hours"] == 24
        assert isinstance(data["data"], list)
    
    def test_predict_invalid_country(self, client):
        """Test prediction rejects invalid country."""
        response = client.post("/predict", json={
            "horizon": 24,
            "country": "XX",
            "levels": [80, 95]
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_predict_horizon_too_large(self, client):
        """Test prediction rejects horizon > 168."""
        response = client.post("/predict", json={
            "horizon": 200,
            "country": "ES",
            "levels": [80, 95]
        })
        
        assert response.status_code == 422
    
    def test_predict_invalid_confidence_level(self, client):
        """Test prediction rejects invalid confidence levels."""
        response = client.post("/predict", json={
            "horizon": 24,
            "country": "ES",
            "levels": [80, 150]  # 150 > 99
        })
        
        assert response.status_code == 422
    
    def test_predict_default_values(self, client, mock_model, mock_requests_get):
        """Test prediction uses default values when not specified."""
        import pandas as pd
        
        # Setup mocks
        mock_model.make_future_dataframe.return_value = pd.DataFrame({
            'unique_id': ['ES']*24,
            'ds': pd.date_range('2025-01-01', periods=24, freq='h')
        })
        
        forecast_df = pd.DataFrame({
            'unique_id': ['ES']*24,
            'ds': pd.date_range('2025-01-01', periods=24, freq='h'),
            'CatBoost': [3000]*24
        })
        mock_model.predict.return_value = forecast_df
        
        with patch('src.api.main.model', mock_model):
            response = client.post("/predict", json={})
            
            assert response.status_code == 200
            data = response.json()
            assert data["horizon_hours"] == 24  # Default
            assert data["country"] == "ES"  # Default
