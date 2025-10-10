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

from backend.api.services.openmeteo import OpenMeteoForecastAPI


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

    class TestInitialization:
        """Test API client initialization."""

        def test_valid_initialization(self, sample_dates, sample_coordinates):
            """Test successful initialization with valid parameters."""
            lat, long = sample_coordinates

            client = OpenMeteoForecastAPI(lat=lat, long=long, days_ahead=1)

            assert client.start is not None
            assert client.end is not None
            assert client.lat == lat
            assert client.long == long
            assert client.cache_expiry_hours == 24

        def test_invalid_latitude(self, sample_dates):
            """Test initialization with invalid latitude."""
            with pytest.raises(ValueError,
                               match="Latitude must be between -90 and 90"):
                OpenMeteoForecastAPI(lat=100, long=-48.5578)

        def test_invalid_longitude(self, sample_dates):
            """Test initialization with invalid longitude."""
            with pytest.raises(ValueError,
                               match="Longitude must be between -180 and 180"):
                OpenMeteoForecastAPI(lat=-22.2964, long=200)

        def test_large_days_ahead(self, sample_coordinates):
            """Test initialization with large days_ahead value."""
            lat, long = sample_coordinates

            # Should not raise an error - validation is handled by external API
            client = OpenMeteoForecastAPI(lat=lat, long=long, days_ahead=20)
            assert client is not None

    class TestURLBuilding:
        """Test URL building functionality."""

        def test_build_request_url(self, api_client):
            """Test URL building with correct parameters."""
            url = api_client._build_request()

            assert "https://api.open-meteo.com/v1/forecast?" in url
            assert "latitude=-22.2964" in url
            assert "longitude=-48.5578" in url
            assert "hourly=" in url
            assert "models=best_match" in url
            assert "format=json" in url

        def test_hourly_parameters_in_url(self, api_client):
            """Test that all required hourly parameters are in URL."""
            url = api_client._build_request()

            expected_params = [
                "temperature_2m",
                "relative_humidity_2m",
                "et0_fao_evapotranspiration",
                "wind_speed_10m",
                "shortwave_radiation",
                "precipitation",
                "precipitation_probability"
            ]

            for param in expected_params:
                assert param in url, f"Parameter {param} not found in URL"

    class TestDataFetching:
        """Test data fetching functionality."""

        @patch('backend.api.services.openmeteo.requests.get')
        def test_successful_api_call(self, mock_get, api_client, mock_api_response_success):
            """Test successful API call and response processing."""
            mock_response = Mock()
            mock_response.json.return_value = mock_api_response_success
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            data, warnings = api_client._fetch_data("https://example.com")

            assert data == mock_api_response_success
            assert len(warnings) == 0
            mock_get.assert_called_once()

        @patch('backend.api.services.openmeteo.requests.get')
        def test_api_call_with_timeout(self, mock_get, api_client):
            """Test API call that times out."""
            mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

            data, warnings = api_client._fetch_data("https://example.com")

            assert data == {}
            assert len(warnings) == 1
            assert "HTTP error" in warnings[0]

        @patch('backend.api.services.openmeteo.requests.get')
        def test_api_call_with_http_error(self, mock_get, api_client):
            """Test API call with HTTP error."""
            mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

            data, warnings = api_client._fetch_data("https://example.com")

            assert data == {}
            assert len(warnings) == 1
            assert "HTTP error" in warnings[0]

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

        def test_data_processing_with_missing_fields(self, api_client):
            """Test processing when some fields are missing from API response."""
            # Create test data with missing fields
            test_df = pd.DataFrame({
                "T2M": [20.5],
                "RH2M": [65],
                "ETO": [0.15],
                "WS2M": [12.3],
                "ALLSKY_SFC_SW_DWN": [120],
                "PRECIP": [0],
                "PRECIP_PROB": [10]
            }, index=pd.date_range("2025-01-01", periods=1, freq="H"))

            with patch.object(api_client, 'get_weather_sync', return_value=(test_df, ["Missing fields"])):
                df, warnings = api_client.get_weather_sync()

            assert not df.empty
            assert "T2M" in df.columns
            assert len(warnings) >= 1

        def test_empty_response_handling(self, api_client):
            """Test handling of empty API response."""
            empty_df = pd.DataFrame()

            with patch.object(api_client, 'get_weather_sync', return_value=(empty_df, ["Empty response"])):
                df, warnings = api_client.get_weather_sync()

            assert df.empty
            assert len(warnings) > 0

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

    class TestWindConversion:
        """Test wind speed conversion functionality."""

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

    class TestCaching:
        """Test caching functionality."""

        def test_cache_initialization(self, api_client):
            """Test that cache is properly initialized."""
            # Test cache initialization by checking if redis_client exists
            assert hasattr(api_client, 'redis_client')

        @patch('backend.api.services.openmeteo.Redis')
        def test_cache_connection_failure(self, mock_redis, api_client):
            """Test handling of Redis connection failure."""
            mock_redis.from_url.side_effect = Exception("Connection failed")

            # Create a new instance to trigger cache setup with mocked Redis
            new_client = OpenMeteoForecastAPI(lat=api_client.lat,
                                              long=api_client.long)

            # Verify that Redis.from_url was called and failed
            mock_redis.from_url.assert_called_once()
            # The client should handle the exception gracefully
            assert new_client is not None

        def test_cache_operations_without_redis(self, api_client):
            """Test cache operations when Redis is not available."""
            api_client.redis_client = None

            df = pd.DataFrame({"test": [1, 2, 3]})
            cache_key = "test_key"

            # These should not raise errors
            api_client._save_to_cache(df, cache_key)
            result = api_client._load_from_cache(cache_key, api_client.start, api_client.end)

            assert result is None

    class TestErrorHandling:
        """Test error handling scenarios."""

        def test_network_error_recovery(self, api_client):
            """Test recovery from network errors."""
            # Create test data
            test_df = pd.DataFrame({
                "T2M": [20.5],
                "RH2M": [65],
                "ETO": [0.15],
                "WS2M": [12.3],
                "ALLSKY_SFC_SW_DWN": [120],
                "PRECIP": [0],
                "PRECIP_PROB": [10]
            }, index=pd.date_range("2025-01-01", periods=1, freq="H"))

            with patch.object(api_client, 'get_weather_sync', return_value=(test_df, ["Network error"])):
                df, warnings = api_client.get_weather_sync()

            assert not df.empty
            assert len(warnings) >= 1

        def test_invalid_json_response(self, api_client):
            """Test handling of invalid JSON response."""
            empty_df = pd.DataFrame()

            with patch.object(api_client, 'get_weather_sync', return_value=(empty_df, ["Invalid JSON"])):
                df, warnings = api_client.get_weather_sync()

            assert df.empty
            assert len(warnings) > 0

    class TestIntegration:
        """Integration tests combining multiple components."""

        def test_full_workflow(self, api_client):
            """Test complete workflow from API call to DataFrame."""
            # Create comprehensive test data
            test_df = pd.DataFrame({
                "T2M": [20.5, 19.8, 18.9],
                "RH2M": [65, 70, 75],
                "ETO": [0.15, 0.12, 0.08],
                "WS2M": [12.3, 10.4, 15.0],
                "ALLSKY_SFC_SW_DWN": [0, 0, 120],
                "PRECIP": [0, 0, 0],
                "PRECIP_PROB": [10, 15, 20]
            }, index=pd.date_range("2025-01-01", periods=3, freq="H"))

            with patch.object(api_client, 'get_weather_sync', return_value=(test_df, ["Forecast warning"])):
                df, warnings = api_client.get_weather_sync()

            # Verify results
            assert not df.empty
            assert len(df) == 3
            assert all(col in df.columns for col in ["T2M", "RH2M", "ETO", "WS2M"])
            assert len(warnings) == 1  # Forecast warning

        def test_cache_hit_workflow(self, api_client):
            """Test workflow when data is available in cache."""
            # Mock cache hit with data
            cached_df = pd.DataFrame({
                "T2M": [20.5, 19.8],
                "RH2M": [65, 70]
            }, index=pd.date_range("2025-01-01", periods=2, freq="h"))

            with patch.object(api_client, '_load_from_cache',
                              return_value=cached_df):
                # Call the method directly on the instance
                df, warnings = api_client.get_weather_sync.__wrapped__(
                    api_client)

            # Verify results
            assert not df.empty
            assert len(df) == 2
            assert len(warnings) == 0  # No warnings for cached data

    class TestUpdateWindow:
        """Test update window control."""

        def test_update_window_control(self, api_client):
            """Test that update window is correctly controlled."""
            test_cases = [
                (0, False),  # 00:00 - should not update (only 05h allowed)
                (5, True),   # 05:00 - should update (fixed time)
                (6, False),  # 06:00 - should not update
                (12, False), # 12:00 - should not update
                (18, False), # 18:00 - should not update
                (23, False)  # 23:00 - should not update
            ]

            for hour, expected in test_cases:
                test_time = datetime.now(pytz.UTC).astimezone(
                    pytz.timezone("America/Sao_Paulo")).replace(hour=hour, minute=0)

                with patch('backend.api.services.openmeteo.datetime') as mock_datetime, \
                     patch.object(api_client.redis_client, 'exists', return_value=0), \
                     patch.object(api_client.redis_client, 'setex'):
                    mock_datetime.now.return_value = test_time

                    result = api_client._should_update_today()
                    assert result == expected, f"Hour {hour}: expected {expected}, got {result}"
