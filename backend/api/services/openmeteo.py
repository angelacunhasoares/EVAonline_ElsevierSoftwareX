import os
import pickle
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import pytz
import requests
from celery import shared_task
from loguru import logger
from redis import Redis
from requests.exceptions import RequestException

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
# Default for Docker


class OpenMeteoAPI:
    """Base class for OpenMeteo API clients.

    Provides common functionality for OpenMeteo Archive and Forecast APIs
    including
    coordinate validation, caching, data validation, and request handling.

    Attributes:
        start (datetime): Start date for weather data.
        end (datetime): End date for weather data.
        lat (float): Latitude (-90 to 90).
        long (float): Longitude (-180 to 180).
        cache_expiry_hours (int): Cache expiry time in hours.
        timezone (str): Detected timezone.

    Raises:
        ValueError: If coordinates or dates are invalid.
    """
    def __init__(
        self,
        start: Union[datetime, date],
        end: Union[datetime, date],
        long: float,
        lat: float,
        cache_expiry_hours: int = 24
    ) -> None:
        """Initialize base OpenMeteo API client.

        Args:
            start: Start date for data.
            end: End date for data.
            long: Longitude (-180 to 180).
            lat: Latitude (-90 to 90).
            cache_expiry_hours: Cache expiry in hours.

        Raises:
            ValueError: If end date is not after start date.
        """
        self.start = (
            start if isinstance(start, datetime)
            else datetime.combine(start, datetime.min.time(), tzinfo=pytz.UTC)
        )
        self.end = (
            end if isinstance(end, datetime)
            else datetime.combine(end, datetime.min.time(), tzinfo=pytz.UTC)
        )
        if self.end <= self.start:
            raise ValueError("End date must be after start date")

        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90 degrees")
        if not (-180 <= long <= 180):
            raise ValueError("Longitude must be between -180 and 180 degrees")

        self.long = long
        self.lat = lat
        self.cache_expiry_hours = cache_expiry_hours

        try:
            self.redis_client = Redis.from_url(REDIS_URL, decode_responses=False)
            self.redis_client.ping()
        except Exception as e:
            logger.error("Failed to connect to Redis: %s", e)
            self.redis_client = None

    def _fetch_data(self, url: str, timeout: int = 10) -> Tuple[dict, List[str]]:
        """Make a synchronous request to the OpenMeteo API with retry.

        Args:
            url: Complete URL with all parameters.
            timeout: Request timeout in seconds (default: 10).

        Returns:
            Tuple[dict, List[str]]: API response data and warnings.
        """
        warnings = []
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json(), warnings
        except RequestException as e:
            msg = f"HTTP error from OpenMeteo API: {e}"
            logger.error("%s at URL: %s", msg, url)
            warnings.append(msg)
            return {}, warnings
        except Exception as e:
            msg = f"Unexpected error querying API: {e}"
            logger.error("%s at URL: %s", msg, url)
            warnings.append(msg)
            return {}, warnings

    def build_url(self) -> str:
        """Build API URL. Must be implemented by subclasses.

        Raises:
            NotImplementedError: Always, to force subclasses to implement.
        """
        raise NotImplementedError("build_url() must be implemented by subclasses")

    def _save_to_cache(self, df: pd.DataFrame, cache_key: str) -> None:
        """Save DataFrame to Redis cache."""
        if not self.redis_client:
            return
        try:
            cached_data = pickle.dumps(df)
            self.redis_client.setex(
                cache_key, timedelta(hours=self.cache_expiry_hours), cached_data
            )
            logger.info("Data saved to cache: %s", cache_key)
        except Exception as e:
            logger.error("Failed to save to cache: %s", e)

    def _load_from_cache(
        self, cache_key: str, start: datetime, end: datetime
    ) -> Optional[pd.DataFrame]:
        """Load DataFrame from Redis cache."""
        if not self.redis_client:
            return None
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data is None:
                return None

            # Handle Redis response type (bytes)
            if isinstance(cached_data, bytes):
                df = pickle.loads(cached_data)
            elif isinstance(cached_data, str):
                df = pickle.loads(cached_data.encode('utf-8'))
            else:
                df = pickle.loads(bytes(str(cached_data), 'utf-8'))

            logger.info("Data loaded from cache: %s", cache_key)
            return df[(df.index >= start) & (df.index <= end)].sort_index()
        except Exception as e:
            logger.error("Failed to load from cache: %s", e)
            return None

    def _get_timezone_from_coords(self) -> str:
        """Return default timezone for Matopiba."""
        logger.warning("Using default timezone America/Sao_Paulo due to "
                       "timezonefinder issues.")
        return "America/Sao_Paulo"


class OpenMeteoForecastAPI(OpenMeteoAPI):
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast?"
    FORECAST_CACHE_EXPIRY_HOURS = 24

    VALID_PARAMETERS = {
        "temperature_2m": (-100, 100),
        "relative_humidity_2m": (0, 100),
        "et0_fao_evapotranspiration": (0, 50),
        "wind_speed_10m": (0, 100),
        "shortwave_radiation": (0, 1500),
        "precipitation": (0, 100),
        "precipitation_probability": (0, 100)
    }

    def __init__(self, lat: float, long: float, days_ahead: int = 1):
        """Initialize the Open-Meteo Forecast API client for today and tomorrow.

        Args:
            lat: Latitude (-90 to 90).
            long: Longitude (-180 to 180).
            days_ahead: Number of days ahead to fetch (default: 1 for tomorrow).
        """
        today = datetime.now(pytz.UTC).astimezone(
            pytz.timezone("America/Sao_Paulo")).date()
        start_date = today
        end_date = today + timedelta(days=days_ahead + 1)  # Include tomorrow
        super().__init__(start_date, end_date, long, lat, self.FORECAST_CACHE_EXPIRY_HOURS)
        self.timezone = self._get_timezone_from_coords()

    def _should_update_today(self) -> bool:
        """Determine if we should update data for today (fixed at 05h)."""
        now = datetime.now(pytz.UTC).astimezone(pytz.timezone("America/Sao_Paulo"))
        current_hour = now.hour
        in_update_window = current_hour == 5  # Fixed at 05h
        today_str = now.strftime("%Y%m%d")
        cache_key = f"last_update:{today_str}:{self.lat}:{self.long}"

        if not self.redis_client:
            return in_update_window

        already_updated = self.redis_client.exists(cache_key)
        should_update = in_update_window and not already_updated
        if should_update:
            self.redis_client.setex(cache_key, timedelta(hours=24), "1")
        return should_update

    def _build_request(self) -> str:
        """Build the Open-Meteo Forecast API request URL."""
        return (
            f"{self.FORECAST_URL}latitude={self.lat}&longitude={self.long}"
            f"&start_date={self.start.strftime('%Y-%m-%d')}"
            f"&end_date={self.end.strftime('%Y-%m-%d')}"
            "&hourly=temperature_2m,relative_humidity_2m,"
            "et0_fao_evapotranspiration,wind_speed_10m,"
            "shortwave_radiation,precipitation,precipitation_probability"
            f"&timezone={self.timezone}"
            "&format=json&models=best_match"
        )

    def build_url(self) -> str:
        """Build the Open-Meteo Forecast API request URL."""
        return self._build_request()

    @shared_task
    def get_weather_sync(self) -> Tuple[pd.DataFrame, List[str]]:
        """Fetch weather data for today and tomorrow."""
        logger.info(
            "Verifying forecast data for lat=%s, long=%s, timezone=%s",
            self.lat, self.long, self.timezone
        )
        today_str = datetime.now(pytz.UTC).astimezone(pytz.timezone("America/Sao_Paulo")).strftime("%Y%m%d")
        cache_key = f"forecast:{today_str}:{self.lat}:{self.long}:{self.timezone}"
        warnings = []

        df = self._load_from_cache(cache_key, self.start, self.end)
        if df is not None:
            logger.info("Data found in cache")
            return df, warnings

        if not self._should_update_today():
            logger.info("Update not needed today or outside 00h-06h window")
            return pd.DataFrame(), ["Update scheduled for 00h-06h"]

        logger.info("Fetching forecast data for lat=%s, long=%s", self.lat, self.long)
        url = self._build_request()
        data, fetch_warnings = self._fetch_data(url)
        warnings.extend(fetch_warnings)
        logger.debug("API Forecast data: %s", data)

        if not (data and "hourly" in data and "time" in data["hourly"]):
            msg = "Invalid API Forecast response"
            logger.error(msg)
            warnings.append(msg)
            return pd.DataFrame(), warnings

        hourly_data = data["hourly"]
        expected_keys = list(self.VALID_PARAMETERS.keys())
        missing_keys = [k for k in expected_keys if k not in hourly_data]
        if missing_keys:
            msg = f"Missing fields: {missing_keys}"
            warnings.append(msg)
            logger.warning(msg)

        try:
            dates = pd.to_datetime(hourly_data["time"])
            len_dates = len(dates)
            na_array = [np.nan] * len_dates
            df = pd.DataFrame({
                "date": dates,
                "T2M": hourly_data.get("temperature_2m", na_array), # Instant/ °C (°F)
                "RH2M": hourly_data.get("relative_humidity_2m", na_array), # Instant/ %
                "ETO": hourly_data.get("et0_fao_evapotranspiration", na_array), # Preceding hour sum/ mm (inch)
                "WS10M": hourly_data.get("wind_speed_10m", na_array), # Instant/ km/h (mph, m/s, knots)
                "ALLSKY_SFC_SW_DWN": hourly_data.get("shortwave_radiation", na_array), # Preceding hour mean/ W/m²
                "PRECIP": hourly_data.get("precipitation", na_array), # Preceding hour sum/ mm (inch)
                "PRECIP_PROB": hourly_data.get("precipitation_probability", na_array) # Preceding hour probability/ %
            }).set_index("date")

            if "shortwave_radiation" in hourly_data and df["ALLSKY_SFC_SW_DWN"].mean() < 1:
                msg = f"Low solar radiation values: {df['ALLSKY_SFC_SW_DWN'].mean():.1f} W/m²"
                warnings.append(msg)
                logger.warning(msg)

            def adjust_wind(ws: float) -> float:
                # Convert wind speed from 10m to 2m using logarithmic profile
                # For neutral stability, u2 = u10 * (2/10)^0.14 ≈ u10 * 0.81
                return ws * 0.81 if not pd.isna(ws) else np.nan
            df["WS2M"] = df["WS10M"].apply(adjust_wind)
            df = df.drop(columns=["WS10M"])

            # Convert solar radiation from W/m² to MJ/m²
            # 1 W/m² = 0.0036 MJ/m² for hourly data
            def convert_radiation(rad: float) -> float:
                return rad * 0.0036 if not pd.isna(rad) else np.nan
            df["ALLSKY_SFC_SW_DWN"] = df["ALLSKY_SFC_SW_DWN"].apply(
                convert_radiation)

            df = df[(df.index >= self.start) &
                    (df.index <= self.end)].sort_index()
            self._save_to_cache(df, cache_key)

            warnings.append(
                "Forecast data may be less reliable as projections. "
                "Updated once daily between 00h-06h.")
            logger.info("Forecast data updated successfully")
            return df, warnings

        except Exception as e:
            msg = f"Error processing forecast data: {e}"
            logger.error(msg)
            warnings.append(msg)
            return pd.DataFrame(), warnings


@shared_task
def get_openmeteo_elevation(
    lat: float, long: float
) -> Tuple[float, List[str]]:
    """Get elevation data from the OpenMeteo Elevation API.

    Args:
        lat: Latitude (-90 to 90).
        long: Longitude (-180 to 180).

    Returns:
        Tuple[float, List[str]]: Elevation in meters and warnings list.

    Example:
        >>> elev, warns = get_openmeteo_elevation(lat=-10.0, long=-45.0)
        >>> print(elev, warns)
        500.0, []
    """
    warnings = []

    # Validate coordinates
    if not (-90 <= lat <= 90):
        msg = "Latitude must be between -90 and 90 degrees"
        logger.error(msg)
        warnings.append(msg)
        return 0.0, warnings

    if not (-180 <= long <= 180):
        msg = "Longitude must be between -180 and 180 degrees"
        logger.error(msg)
        warnings.append(msg)
        return 0.0, warnings

    # Cache key and settings
    cache_key = f"elevation:{lat}:{long}"
    cache_expiry_hours = 24  # 24 hours

    # Initialize Redis client
    redis_client = None
    try:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        msg = f"Failed to connect to Redis: {e}. Continuing without cache."
        logger.warning(msg)
        warnings.append(msg)
        # Don't return here - continue to fetch from API

    # Check cache only if Redis is available
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                # Handle Redis response type (bytes or str)
                if isinstance(cached_data, bytes):
                    elevation_str = cached_data.decode('utf-8')
                elif isinstance(cached_data, str):
                    elevation_str = cached_data
                else:
                    elevation_str = str(cached_data)

                elevation = float(elevation_str)
                if -1000 <= elevation <= 9000:
                    logger.info(
                        "Loaded elevation from cache: %s meters",
                        elevation
                    )
                    return elevation, warnings

                msg = f"Invalid cached elevation: {elevation}"
                warnings.append(msg)
                logger.warning(msg)

        except Exception as e:
            msg = f"Error accessing Redis cache: {e}"
            warnings.append(msg)
            logger.error(msg)

    # Exemplo de URL, Jaú, SP, Brasil:
    # https://api.open-meteo.com/v1/elevation?latitude=-22.2964&longitude=-48.5578
    url = (
        "https://api.open-meteo.com/v1/elevation?"
        f"latitude={lat}&longitude={long}"
    )
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("elevation"):
            msg = "API returned no elevation data"
            logger.error(msg)
            warnings.append(msg)
            return 0.0, warnings

        elevation = data["elevation"][0]
        if not isinstance(elevation, (int, float)):
            msg = f"Invalid elevation type: {type(elevation)}"
            logger.error(msg)
            warnings.append(msg)
            return 0.0, warnings

        if elevation < -1000 or elevation > 9000:
            msg = f"Elevation out of range: {elevation}"
            logger.error(msg)
            warnings.append(msg)
            return 0.0, warnings

        # Save to cache only if Redis is available
        if redis_client:
            try:
                redis_client.setex(
                    cache_key,
                    timedelta(hours=cache_expiry_hours),
                    str(elevation)
                )
                logger.info(
                    "Elevation saved to cache: %s meters",
                    elevation
                )
            except Exception as e:
                msg = f"Error saving to cache: {e}"
                warnings.append(msg)
                logger.error(msg)

        logger.info(
            "Elevation fetched (lat=%s, long=%s): %s meters",
            lat, long, elevation
        )
        return float(elevation), warnings

    except RequestException as e:
        msg = f"HTTP error fetching elevation: {e}"
        warnings.append(msg)
        logger.error(msg)
        return 0.0, warnings

    except Exception as e:
        msg = f"Unexpected error: {e}"
        warnings.append(msg)
        logger.error(msg)
        return 0.0, warnings
