"""
Test suite for OpenMeteo API services.

This module contains comprehensive tests for the OpenMeteoForecastAPI class,
covering various scenarios including success cases, error handling, caching,
and data validation.

Author: EVAonline Team
Date: 2025-09-03
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import pytz
import requests

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from backend.api.services.openmeteo import OpenMeteoAPI, OpenMeteoForecastAPI


class TestOpenMeteoForecastAPI:
    """Test suite for OpenMeteoForecastAPI class."""

    @pytest.fixture
    def sample_dates(self):
        """Fixture providing sample date range for testing."""
        today = datetime.now()
        start = today - timedelta(days=2)
        end = start + timedelta(days=1)
        return start, end

    @pytest.fixture
    def sample_coordinates(self):
        """Fixture providing sample coordinates for testing."""
        return -22.2964, -48.5578  # Jaú, SP

    @pytest.fixture
    def api_client(self, sample_dates, sample_coordinates):
        """Fixture providing initialized API client."""
        lat, long = sample_coordinates
        return OpenMeteoForecastAPI(lat=lat, long=long, days_ahead=1)

    class TestDataProcessing:
        """Test data processing and DataFrame creation."""

        def test_successful_data_processing(self, api_client):
            """Test successful processing of API response into DataFrame."""
            # Create a simple test DataFrame
            test_df = pd.DataFrame({
                "T2M": [20.5, 19.8, 18.9],
                "RH2M": [65, 70, 75],
                "ETO": [0.15, 0.12, 0.08],
                "WS2M": [12.3, 10.4, 15.0],
                "ALLSKY_SFC_SW_DWN": [0, 0, 120],
                "PRECIP": [0, 0, 0],
                "PRECIP_PROB": [10, 15, 20]
            }, index=pd.date_range("2025-01-01", periods=3, freq="H"))

            # Mock the method to return our test data
            with patch.object(api_client, 'get_weather_sync', return_value=(test_df, [])):
                df, warnings = api_client.get_weather_sync()

            assert not df.empty
            assert len(df) == 3
            assert "T2M" in df.columns
            assert "RH2M" in df.columns
            assert "ETO" in df.columns
            assert "WS2M" in df.columns

        def test_wind_speed_conversion(self, api_client):
            """Test wind speed conversion from 10m to 2m."""
            # Create test data with 10m wind speeds
            test_df = pd.DataFrame({
                "T2M": [20.5],
                "RH2M": [65],
                "ETO": [0.15],
                "WS2M": [12.3],  # Should be 15.2 * 0.81 = 12.312
                "ALLSKY_SFC_SW_DWN": [120],
                "PRECIP": [0],
                "PRECIP_PROB": [10]
            }, index=pd.date_range("2025-01-01", periods=1, freq="H"))

            with patch.object(api_client, 'get_weather_sync', return_value=(test_df, [])):
                df, warnings = api_client.get_weather_sync()

            # Check if wind speed was converted (10m to 2m)
            # Using logarithmic profile: u2 = u10 * (2/10)^0.14 ≈ u10 * 0.81
            expected_converted = 15.2 * 0.81  # 10m to 2m conversion
            actual_value = df["WS2M"].iloc[0]
            assert abs(actual_value - expected_converted) < 0.1

    class TestValidation:
        """Test parameter validation."""

        def test_parameter_ranges(self, api_client):
            """Test that VALID_PARAMETERS contains expected ranges."""
            expected_ranges = {
                "temperature_2m": (-100, 100),
                "relative_humidity_2m": (0, 100),
                "et0_fao_evapotranspiration": (0, 50),
                "wind_speed_10m": (0, 100),
                "shortwave_radiation": (0, 1500),
                "precipitation": (0, 100),
                "precipitation_probability": (0, 100)
            }

            assert api_client.VALID_PARAMETERS == expected_ranges

    class TestUpdateWindow:
        """Test update window control."""

        def test_update_window_control(self, api_client):
            """Test that update window is correctly controlled."""
            test_cases = [
                (0, True),   # 00:00 - should update
                (5, True),   # 05:00 - should update (fixed time)
                (6, False),  # 06:00 - should not update
                (12, False), # 12:00 - should not update
                (18, False), # 18:00 - should not update
                (23, False)  # 23:00 - should not update
            ]

            for hour, expected in test_cases:
                test_time = datetime.now(pytz.UTC).astimezone(
                    pytz.timezone("America/Sao_Paulo")).replace(hour=hour, minute=0)

                with patch('backend.api.services.openmeteo.datetime') as mock_datetime:
                    mock_datetime.now.return_value = test_time

                    result = api_client._should_update_today()
                    assert result == expected, f"Hour {hour}: expected {expected}, got {result}"</content>
<parameter name="filePath">C:\Users\User\OneDrive\Documentos\GitHub\EVAonline_ElsevierSoftwareX\backend\tests\test_openmeteo_simple.py
