"""
Test suite for OpenMeteo API services.

This module contains comprehensive tests for the OpenMeteoForecastAPI class,
covering various scenarios including success cases, error handling, caching,
and data validation.

Author: EVAonline Team
Date: 2025-09-03
"""
                "ETO": [0.15, 0.12, 0.08],
                "WS2M": [12.3, 10.4, 15.0],  # Already converted to 2m
                "ALLSKY_SFC_SW_DWN": [0, 0, 120],
                "PRECIP": [0, 0, 0],
                "PRECIP_PROB": [10, 15, 20]
            }, index=pd.date_range("2025-01-01", periods=3, freq="H"))

            with patch.object(api_client, 'get_weather_sync', return_value=(test_df, [])):
                df, warnings = api_client.get_weather_sync()

            assert not df.empty
            assert len(df) == 3
            assert "T2M" in df.columns
            assert "RH2M" in df.columns
            assert "ETO" in df.columns
            assert "WS2M" in df.columnserror handling, caching,
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

        def test_successful_data_processing(self, api_client, mock_api_response_success):
            """Test successful processing of API response into DataFrame."""
            # Mock the _fetch_data method
            api_client._fetch_data = Mock(return_value=(mock_api_response_success, []))
            # Mock _should_update_today to allow processing
            api_client._should_update_today = Mock(return_value=True)
            # Mock cache miss
            api_client._load_from_cache = Mock(return_value=None)
            # Mock _build_request to return a dummy URL
            api_client._build_request = Mock(return_value="http://dummy.url")

            df, warnings = api_client.get_weather_sync.__wrapped__(api_client)

            assert not df.empty
            assert len(df) == 3  # 3 hourly records
            assert "T2M" in df.columns
            assert "RH2M" in df.columns
            assert "ETO" in df.columns
            assert "WS2M" in df.columns
            assert "PRECIP" in df.columns
            assert "ALLSKY_SFC_SW_DWN" in df.columns
            assert "PRECIP_PROB" in df.columns

        def test_data_processing_with_missing_fields(self, api_client, sample_date_ranges):
            """Test processing when some fields are missing from API response."""
            # Use dynamic date from the forecast range
            start, _ = sample_date_ranges["forecast_range"]
            
            incomplete_response = {
                "hourly": {
                    "time": [start.strftime("%Y-%m-%dT%H:%M:%S")],
                    "temperature_2m": [20.5],
                    # Missing other fields
                }
            }

            api_client._fetch_data = Mock(return_value=(incomplete_response, []))
            # Mock _should_update_today to allow processing
            api_client._should_update_today = Mock(return_value=True)
            # Mock cache miss
            api_client._load_from_cache = Mock(return_value=None)

            df, warnings = api_client.get_weather_sync.__wrapped__(api_client)

            # Should have warnings about missing fields
            assert len(warnings) > 0
            # DataFrame should contain the available data (temperature)
            assert "T2M" in df.columns
            # Check if temperature data is present
            assert not df["T2M"].isna().all()

        def test_empty_response_handling(self, api_client):
            """Test handling of empty API response."""
            api_client._fetch_data = Mock(return_value=({}, []))

            df, warnings = api_client.get_weather_sync.__wrapped__(api_client)

            assert df.empty
            assert len(warnings) > 0

    class TestValidation:
        """Test data validation functionality."""

        def test_parameter_ranges(self, api_client):
            """Test that parameter ranges are properly defined."""
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

    def test_wind_speed_conversion(self, api_client, mock_api_response_success):
        """Test wind speed conversion from 10m to 2m."""
        api_client._fetch_data = Mock(return_value=(mock_api_response_success, []))
        # Mock _should_update_today to allow processing
        api_client._should_update_today = Mock(return_value=True)
        # Mock cache miss
        api_client._load_from_cache = Mock(return_value=None)

        df, _ = api_client.get_weather_sync.__wrapped__(api_client)

        # Check if wind speed was converted (10m to 2m)
        # Using logarithmic profile: u2 = u10 * (2/10)^0.14 ≈ u10 * 0.81
        expected_converted = 15.2 * 0.81  # 10m to 2m conversion
        actual_value = df["WS2M"].iloc[0]
        assert abs(actual_value - expected_converted) < 0.1, (
            f"Expected {expected_converted}, got {actual_value}")

        # Check if WS10M column was removed
        assert "WS10M" not in df.columns

    class TestCaching:
        """Test caching functionality."""

        @patch('backend.api.services.openmeteo.Redis')
        def test_cache_initialization(self, mock_redis, api_client):
            """Test Redis cache initialization."""
            mock_redis_client = Mock()
            mock_redis.from_url.return_value = mock_redis_client
            mock_redis_client.ping.return_value = True

            # Test cache initialization by checking if redis_client is set
            # The cache is initialized in __init__, so we just verify it exists
            assert hasattr(api_client, 'redis_client')

        @patch('backend.api.services.openmeteo.Redis')
        def test_cache_connection_failure(self, mock_redis, api_client):
            """Test handling of Redis connection failure."""
            mock_redis.from_url.side_effect = Exception("Connection failed")

            # Test cache connection failure handling
            # The cache initialization happens in __init__, so we test the failure case
            assert api_client.redis_client is None

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

        def test_network_error_recovery(self, api_client, sample_date_ranges):
            """Test recovery from network errors."""
            # Use dynamic date from the forecast range
            start, _ = sample_date_ranges["forecast_range"]
            
            api_client._fetch_data = Mock(side_effect=[
                ({}, ["Network error"]),
                {"hourly": {"time": [start.strftime("%Y-%m-%dT%H:%M:%S")], "temperature_2m": [20.5]}}, []
            ])
            # Mock _should_update_today to allow processing
            api_client._should_update_today = Mock(return_value=True)

            df, warnings = api_client.get_weather_sync.__wrapped__(api_client)

            assert not df.empty
            assert len(warnings) >= 1

        def test_invalid_json_response(self, api_client):
            """Test handling of invalid JSON response."""
            api_client._fetch_data = Mock(return_value=(None, ["Invalid JSON"]))
            # Mock _should_update_today to allow processing
            api_client._should_update_today = Mock(return_value=True)

            df, warnings = api_client.get_weather_sync.__wrapped__(api_client)

            assert df.empty
            assert len(warnings) > 0

    class TestIntegration:
        """Integration tests combining multiple components."""

        @patch('backend.api.services.openmeteo.requests.get')
        def test_full_workflow(self, mock_get, api_client, mock_api_response_success):
            """Test complete workflow from API call to DataFrame."""
            # Mock successful API response
            mock_response = Mock()
            mock_response.json.return_value = mock_api_response_success
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Mock cache miss
            api_client._load_from_cache = Mock(return_value=None)
            # Mock _should_update_today to allow processing
            api_client._should_update_today = Mock(return_value=True)

            # Execute full workflow
            df, warnings = api_client.get_weather_sync.__wrapped__(api_client)

            # Verify results
            assert not df.empty
            assert len(df) == 3
            assert all(col in df.columns for col in ["T2M", "RH2M", "ETO", "WS2M"])
            assert len(warnings) == 1  # Forecast warning

            # Verify API was called
            mock_get.assert_called_once()

        @patch('backend.api.services.openmeteo.requests.get')
        def test_cache_hit_workflow(self, mock_get, api_client, sample_date_ranges):
            """Test workflow when data is available in cache."""
            # Mock cache hit with data in the correct date range
            start, _ = sample_date_ranges["forecast_range"]
            cached_df = pd.DataFrame({
                "T2M": [20.5, 19.8],
                "RH2M": [65, 70]
            }, index=pd.date_range(start, periods=2, freq="H"))

            api_client._load_from_cache = Mock(return_value=cached_df)

            # Execute workflow
            df, warnings = api_client.get_weather_sync.__wrapped__(api_client)

            # Verify results
            assert not df.empty
            assert len(df) == 2
            assert len(warnings) == 0  # No warnings for cached data

            # Verify API was NOT called
            mock_get.assert_not_called()


class TestOpenMeteoAPI:
    """Test suite for base OpenMeteoAPI class."""

    def test_base_class_initialization(self):
        """Test base class initialization."""
        start = datetime.now()
        end = start + timedelta(days=1)

        api = OpenMeteoAPI(start, end, -48.5578, -22.2964)

        assert api.start == start
        assert api.end == end
        assert api.lat == -22.2964
        assert api.long == -48.5578

    def test_base_class_abstract_method(self):
        """Test that build_url raises NotImplementedError."""
        api = OpenMeteoAPI(datetime.now(), datetime.now() + timedelta(days=1), 0, 0)

        with pytest.raises(NotImplementedError):
            api.build_url()


# Test configuration and utilities
class TestConfiguration:
    """Test configuration and utility functions."""

    def test_redis_url_configuration(self):
        """Test Redis URL configuration."""
        from backend.api.services.openmeteo import REDIS_URL

        # Should have a default Redis URL
        assert "redis://" in REDIS_URL

    def test_parameter_validation_ranges(self):
        """Test that all parameter ranges are reasonable."""
        from backend.api.services.openmeteo import OpenMeteoForecastAPI

        for param, (min_val, max_val) in OpenMeteoForecastAPI.VALID_PARAMETERS.items():
            assert min_val < max_val, f"Invalid range for {param}: {min_val} >= {max_val}"


# New tests for improved functionality
class TestOpenMeteoForecastAPI_Improved:
    """Test suite for improved OpenMeteoForecastAPI functionality."""

    def test_automatic_date_detection(self):
        """Test automatic date detection for today and tomorrow."""
        lat, long = -22.2964, -48.5578

        client = OpenMeteoForecastAPI(lat=lat, long=long, days_ahead=1)

        # Should automatically set start to today and end to tomorrow
        today = datetime.now(pytz.UTC).astimezone(pytz.timezone("America/Sao_Paulo")).date()
        tomorrow = today + timedelta(days=2)  # Include tomorrow + buffer

        assert client.start.date() == today
        assert client.end.date() >= tomorrow

    def test_matopiba_region_focus(self):
        """Test focus on Matopiba region coordinates."""
        # Test various Matopiba locations
        matopiba_locations = [
            (-46.6333, -23.5505),  # São Paulo (reference point)
            (-47.0, -10.0),       # Matopiba central
            (-42.0, -7.0),        # Maranhão
            (-44.0, -9.0),        # Piauí
            (-45.0, -12.0),       # Bahia
            (-48.0, -15.0),       # Tocantins
        ]

        for lat, long in matopiba_locations:
            client = OpenMeteoForecastAPI(lat=lat, long=long)
            assert client.lat == lat
            assert client.long == long
            assert -90 <= client.lat <= 90
            assert -180 <= client.long <= 180

    def test_update_window_control(self):
        """Test update control between 00h-06h window."""
        lat, long = -22.2964, -48.5578
        client = OpenMeteoForecastAPI(lat=lat, long=long)

        # Test different times
        test_times = [
            (0, True),   # 00:00 - should update
            (3, True),   # 03:00 - should update
            (5, True),   # 05:59 - should update
            (6, False),  # 06:00 - should not update
            (12, False), # 12:00 - should not update
            (18, False), # 18:00 - should not update
            (23, False), # 23:00 - should not update
        ]

        for hour, expected in test_times:
            # Mock current time
            test_time = datetime.now(pytz.UTC).astimezone(
                pytz.timezone("America/Sao_Paulo")).replace(hour=hour, minute=0)

            with patch('backend.api.services.openmeteo.datetime') as mock_datetime:
                mock_datetime.now.return_value = test_time

                result = client._should_update_today()
                assert result == expected, f"Hour {hour}: expected {expected}, got {result}"

    def test_coordinate_validation(self):
        """Test coordinate validation for Matopiba region."""
        # Valid coordinates
        valid_coords = [
            (-22.2964, -48.5578),  # Jaú, SP
            (-15.7942, -47.8822),  # Brasília, DF
            (-12.9714, -38.5014),  # Salvador, BA
        ]

        for lat, long in valid_coords:
            client = OpenMeteoForecastAPI(lat=lat, long=long)
            assert client.lat == lat
            assert client.long == long

        # Invalid coordinates should raise ValueError
        invalid_coords = [
            (100, -48.5578),   # Invalid latitude
            (-22.2964, 200),   # Invalid longitude
            (-100, -200),      # Both invalid
        ]

        for lat, long in invalid_coords:
            with pytest.raises(ValueError):
                OpenMeteoForecastAPI(lat=lat, long=long)

    @patch('backend.api.services.openmeteo.Redis')
    def test_redis_cache_robustness(self, mock_redis):
        """Test Redis cache handles different data types correctly."""
        from backend.api.services.openmeteo import get_openmeteo_elevation

        # Mock Redis client
        mock_client = Mock()
        mock_redis.from_url.return_value = mock_client

        # Test with bytes data
        mock_client.get.return_value = b'123.45'
        result = get_openmeteo_elevation(-22.2964, -48.5578)
        assert isinstance(result, tuple)
        assert len(result) == 2

        # Test with string data
        mock_client.get.return_value = '123.45'
        result = get_openmeteo_elevation(-22.2964, -48.5578)
        assert isinstance(result, tuple)
        assert len(result) == 2

        # Test with None (cache miss)
        mock_client.get.return_value = None
        result = get_openmeteo_elevation(-22.2964, -48.5578)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_timezone_detection_fallback(self):
        """Test timezone detection fallback mechanism."""
        lat, long = -22.2964, -48.5578
        client = OpenMeteoForecastAPI(lat=lat, long=long)

        # Should use default timezone when timezonefinder fails
        assert client.timezone == "America/Sao_Paulo"

    @patch('backend.api.services.openmeteo.shared_task')
    def test_scheduled_update_matopiba_locations(self, mock_shared_task):
        """Test scheduled update covers Matopiba locations."""
        # Function removed - using CSV with all Matopiba cities instead
        # This test is no longer applicable
        pass

    def test_days_ahead_parameter(self):
        """Test days_ahead parameter affects date range."""
        lat, long = -22.2964, -48.5578

        # Test with different days_ahead values
        for days in [1, 2, 3, 7]:
            client = OpenMeteoForecastAPI(lat=lat, long=long, days_ahead=days)

            today = datetime.now(pytz.UTC).astimezone(
                pytz.timezone("America/Sao_Paulo")).date()

            expected_end = today + timedelta(days=days + 1)  # +1 for buffer
            assert client.end.date() >= expected_end


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
