"""
Simple test for OpenMeteo API wind conversion.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import pytz

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from backend.api.services.openmeteo import OpenMeteoForecastAPI


def test_wind_speed_conversion():
    """Test wind speed conversion from 10m to 2m."""
    # Create API client
    api_client = OpenMeteoForecastAPI(lat=-22.2964, long=-48.5578, days_ahead=1)

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


def test_update_window_control():
    """Test that update window is correctly controlled."""
    api_client = OpenMeteoForecastAPI(lat=-22.2964, long=-48.5578, days_ahead=1)

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
             patch.object(api_client.redis_client, 'setex') as mock_setex:
            mock_datetime.now.return_value = test_time

            result = api_client._should_update_today()
            assert result == expected, f"Hour {hour}: expected {expected}, got {result}"


if __name__ == "__main__":
    test_wind_speed_conversion()
    test_update_window_control()
    print("All tests passed!")
