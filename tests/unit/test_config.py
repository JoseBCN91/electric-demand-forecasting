"""
Unit tests for API configuration and validation.
"""

import pytest
from src.core.config import (
    APISettings,
    validate_horizon,
    validate_country,
    validate_confidence_levels
)


class TestConfigValidation:
    """Test configuration validation functions."""
    
    def test_validate_horizon_valid(self):
        """Test valid horizon values."""
        assert validate_horizon(1) is True
        assert validate_horizon(24) is True
        assert validate_horizon(168) is True
    
    def test_validate_horizon_invalid(self):
        """Test invalid horizon values."""
        assert validate_horizon(0) is False
        assert validate_horizon(-5) is False
        assert validate_horizon(169) is False
        assert validate_horizon(1000) is False
    
    def test_validate_country_valid(self):
        """Test valid country codes."""
        assert validate_country('ES') is True
        assert validate_country('FR') is True
        assert validate_country('DE') is True
        assert validate_country('IT') is True
    
    def test_validate_country_invalid(self):
        """Test invalid country codes."""
        assert validate_country('XX') is False
        assert validate_country('GB') is False
        assert validate_country('us') is False
        assert validate_country('') is False
    
    def test_validate_confidence_levels_valid(self):
        """Test valid confidence levels."""
        assert validate_confidence_levels([80, 95]) is True
        assert validate_confidence_levels([50]) is True
        assert validate_confidence_levels([1, 50, 99]) is True
    
    def test_validate_confidence_levels_invalid(self):
        """Test invalid confidence levels."""
        assert validate_confidence_levels([100]) is False
        assert validate_confidence_levels([0]) is False
        assert validate_confidence_levels([-5, 80]) is False
        assert validate_confidence_levels([]) is False
    
    def test_settings_defaults(self):
        """Test API settings have correct defaults."""
        settings = APISettings()
        
        assert settings.MIN_HORIZON == 1
        assert settings.MAX_HORIZON == 168
        assert settings.DEFAULT_HORIZON == 24
        assert settings.DEFAULT_COUNTRY == 'ES'
        assert len(settings.SUPPORTED_COUNTRIES) == 4
        assert 'ES' in settings.SUPPORTED_COUNTRIES
        assert settings.RATE_LIMIT_REQUESTS == 20
        assert settings.WEATHER_CACHE_TTL_MINUTES == 30
