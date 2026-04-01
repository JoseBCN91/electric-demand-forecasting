"""
Unit tests for API validation and request models.
"""

import pytest
from pydantic import ValidationError
from src.api.main import PredictRequest


class TestPredictRequest:
    """Test prediction request validation."""
    
    def test_valid_request(self):
        """Test valid prediction request."""
        req = PredictRequest(
            horizon=24,
            country='ES',
            levels=[80, 95]
        )
        assert req.horizon == 24
        assert req.country == 'ES'
        assert req.levels == [80, 95]
    
    def test_default_values(self):
        """Test default request values."""
        req = PredictRequest()
        assert req.horizon == 24
        assert req.country == 'ES'
        assert req.levels == [80, 95]
    
    def test_horizon_boundary_valid(self):
        """Test horizon boundary values are valid."""
        req1 = PredictRequest(horizon=1)
        assert req1.horizon == 1
        
        req2 = PredictRequest(horizon=168)
        assert req2.horizon == 168
    
    def test_horizon_too_large(self):
        """Test horizon validation rejects values > 168."""
        with pytest.raises(ValidationError) as exc_info:
            PredictRequest(horizon=169)
        
        assert 'horizon' in str(exc_info.value).lower()
    
    def test_horizon_zero_rejected(self):
        """Test horizon validation rejects zero and negative."""
        with pytest.raises(ValidationError):
            PredictRequest(horizon=0)
        
        with pytest.raises(ValidationError):
            PredictRequest(horizon=-1)
    
    def test_invalid_country(self):
        """Test invalid country code is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PredictRequest(country='XX')
        
        assert 'country' in str(exc_info.value).lower()
    
    def test_invalid_confidence_level_too_high(self):
        """Test confidence levels > 99 are rejected."""
        with pytest.raises(ValidationError):
            PredictRequest(levels=[80, 100])
        
        with pytest.raises(ValidationError):
            PredictRequest(levels=[150])
    
    def test_invalid_confidence_level_zero(self):
        """Test confidence level 0 is rejected."""
        with pytest.raises(ValidationError):
            PredictRequest(levels=[0, 80])
    
    def test_all_countries_valid(self):
        """Test all supported countries are valid."""
        countries = ['ES', 'FR', 'DE', 'IT']
        for country in countries:
            req = PredictRequest(country=country)
            assert req.country == country
    
    def test_multiple_confidence_levels(self):
        """Test multiple confidence levels are accepted."""
        req = PredictRequest(levels=[10, 50, 90, 99])
        assert len(req.levels) == 4
        assert all(1 <= level <= 99 for level in req.levels)
