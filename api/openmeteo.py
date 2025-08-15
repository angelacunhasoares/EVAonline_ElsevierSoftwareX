import asyncio
import json
import os
from datetime import date, datetime, timedelta
from typing import Optional, Union, Tuple
import numpy as np
import pandas as pd
from aiohttp import ClientSession
from celery import shared_task
from redis import Redis
from loguru import logger  # Alterado para loguru
import aiohttp
import pickle

# Configuração do Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

@shared_task
async def get_openmeteo_elevation(lat: float, long: float) -> Tuple[float, list]:
    """
    Fetch elevation data from Open-Meteo Elevation API asynchronously.

    Args:
        lat (float): Latitude (-90 to 90).
        long (float): Longitude (-180 to 180).

    Returns:
        Tuple[float, list]: Elevation in meters and list of warnings.

    Example:
        >>> elevation, warnings = await get_openmeteo_elevation(lat=-10.0, long=-45.0)
        >>> print(elevation, warnings)
        500.0, []
    """
    warnings = []

    # Validate coordinates
    if not (-90 <= lat <= 90):
        warnings.append("Latitude must be between -90 and 90.")
        logger.error(warnings[-1])
        return 0.0, warnings
    if not (-180 <= long <= 180):
        warnings.append("Longitude must be between -180 and 180.")
        logger.error(warnings[-1])
        return 0.0, warnings

    # Cache key
    cache_key = f"elevation:{lat}:{long}"
    cache_expiry_hours = 24  # 24 hours

    # Initialize Redis client
    try:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()  # Test connection
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}. Returning default elevation.")
        warnings.append(f"Redis connection failed: {e}")
        return 0.0, warnings

    # Check cache
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            elevation = float(cached_data)
            if -1000 <= elevation <= 9000:
                logger.info(f"Loaded elevation from Redis cache: {elevation} meters")
                return elevation, warnings
            else:
                warnings.append(f"Invalid cached elevation: {elevation}")
                logger.warning(warnings[-1])
    except Exception as e:
        warnings.append(f"Error accessing Redis cache: {e}")
        logger.error(warnings[-1])

    # Fetch elevation from API
    url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={long}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                data = await response.json()
                if "elevation" not in data or not data["elevation"]:
                    warnings.append("No elevation data returned by Open-Meteo API.")
                    logger.error(warnings[-1])
                    return 0.0, warnings

                elevation = data["elevation"][0]
                if not isinstance(elevation, (int, float)) or elevation < -1000 or elevation > 9000:
                    warnings.append(f"Invalid elevation value returned: {elevation}")
                    logger.error(warnings[-1])
                    return 0.0, warnings

                # Save to cache
                try:
                    redis_client.setex(cache_key, timedelta(hours=cache_expiry_hours), str(elevation))
                    logger.info(f"Saved elevation to Redis cache: {elevation} meters")
                except Exception as e:
                    warnings.append(f"Failed to save to Redis cache: {e}")
                    logger.error(warnings[-1])

                logger.info(f"Elevation obtained for lat={lat}, long={long}: {elevation} meters")
                return float(elevation), warnings

        except aiohttp.ClientResponseError as e:
            warnings.append(f"HTTP error fetching elevation: {e.status} - {e.message}")
            logger.error(warnings[-1])
            return 0.0, warnings
        except asyncio.TimeoutError:
            warnings.append(f"Timeout fetching elevation for lat={lat}, long={long}")
            logger.error(warnings[-1])
            return 0.0, warnings
        except Exception as e:
            warnings.append(f"Unexpected error fetching elevation: {str(e)}")
            logger.error(warnings[-1])
            return 0.0, warnings

class BaseOpenMeteoAPI:
    VALID_PARAMETERS = {
        "temperature_2m_max": "T2M_MAX",
        "temperature_2m_min": "T2M_MIN",
        "temperature_2m_mean": "T2M",
        "relative_humidity_2m_mean": "RH2M",
        "windspeed_10m_mean": "WS10M_MEAN",
        "shortwave_radiation_sum": "ALLSKY_SFC_SW_DWN",
        "precipitation_sum": "PRECTOTCORR",
    }

    def __init__(
        self,
        start: Union[datetime, date],
        end: Union[datetime, date],
        long: float,
        lat: float,
        cache_expiry_hours: int = 24,
    ):
        """
        Initialize the base Open-Meteo API client.

        Args:
            start: Start date (datetime, date, or pd.Timestamp).
            end: End date (datetime, date, or pd.Timestamp).
            long: Longitude (-180 to 180).
            lat: Latitude (-90 to 90).
            cache_expiry_hours: Cache expiration time in hours.

        Raises:
            ValueError: If end date is before start date, or coordinates are invalid.
        """
        # Validate coordinates
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90.")
        if not (-180 <= long <= 180):
            raise ValueError("Longitude must be between -180 and 180.")

        # Validate dates
        self.start = (
            start
            if isinstance(start, datetime)
            else datetime.combine(start, datetime.min.time())
        )
        self.end = (
            end
            if isinstance(end, datetime)
            else datetime.combine(end, datetime.min.time())
        )
        if self.end < self.start:
            raise ValueError("End date must be after start date.")

        self.long = long
        self.lat = lat
        self.cache_expiry_hours = cache_expiry_hours
        self.request_url = self._build_request()

        # Initialize Redis client
        try:
            self.redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
            self.redis_client.ping()  # Test connection
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    async def _fetch_data(self, session: ClientSession, url: str) -> Tuple[dict, list]:
        """
        Make an asynchronous request to the Open-Meteo API.

        Args:
            session: aiohttp ClientSession.
            url: API request URL.

        Returns:
            Tuple[dict, list]: JSON response and list of warnings.
        """
        warnings = []
        try:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                return await response.json(), warnings
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error downloading from {url}: {e.status} - {e.message}")
            warnings.append(f"HTTP error: {e.status} - {e.message}")
            return {}, warnings
        except asyncio.TimeoutError:
            logger.error(f"Timeout downloading from {url}")
            warnings.append(f"Timeout downloading from {url}")
            return {}, warnings
        except Exception as e:
            logger.error(f"Unexpected error downloading from {url}: {e}")
            warnings.append(f"Unexpected error: {e}")
            return {}, warnings

    def _build_request(self) -> str:
        """Build the API request URL (implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement _build_request")

    def _save_to_cache(self, df: pd.DataFrame, cache_key: str) -> None:
        """Save data to Redis cache."""
        if not self.redis_client:
            logger.warning("No Redis connection. Skipping cache save.")
            return
        try:
            self.redis_client.setex(
                cache_key,
                timedelta(hours=self.cache_expiry_hours),
                pickle.dumps(df)
            )
            logger.info(f"Saved to Redis cache: {cache_key}")
        except Exception as e:
            logger.error(f"Failed to save to Redis cache: {e}")

    def _load_from_cache(self, cache_key: str, start: datetime, end: datetime) -> Optional[pd.DataFrame]:
        """Load data from Redis cache if available and valid."""
        if not self.redis_client:
            logger.warning("No Redis connection. Skipping cache load.")
            return None
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                df = pickle.loads(cached_data)
                if df.index.min() <= start and df.index.max() >= end:
                    logger.info(f"Loaded from Redis cache: {cache_key}")
                    return df
                else:
                    logger.info(f"Redis cached data does not cover requested range: {cache_key}")
            else:
                logger.info(f"Redis cache not found: {cache_key}")
        except Exception as e:
            logger.error(f"Failed to load from Redis cache: {e}")
        return None

    async def get_weather(self) -> Tuple[pd.DataFrame, list]:
        """Fetch weather data (implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement get_weather")

class OpenMeteoArchiveAPI(BaseOpenMeteoAPI):
    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive?"
    ARCHIVE_CACHE_EXPIRY_HOURS = 48  # 2 days

    def __init__(
        self,
        start: Union[datetime, date],
        end: Union[datetime, date],
        long: float,
        lat: float,
    ):
        """Initialize the Open-Meteo Archive API client."""
        super().__init__(start, end, long, lat, cache_expiry_hours=self.ARCHIVE_CACHE_EXPIRY_HOURS)

    def _build_request(self) -> str:
        """Build the Open-Meteo Archive API request URL."""
        return (
            f"{self.ARCHIVE_URL}latitude={self.lat}&longitude={self.long}"
            f"&start_date={self.start.strftime('%Y-%m-%d')}&end_date={self.end.strftime('%Y-%m-%d')}"
            "&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
            "relative_humidity_2m_mean,windspeed_10m_mean,shortwave_radiation_sum,precipitation_sum"
            "&format=json&models=ecmwf_ifs025"
        )

    @shared_task
    async def get_weather(self) -> Tuple[pd.DataFrame, list]:
        """
        Fetch daily weather data from Open-Meteo Archive API.

        Returns:
            Tuple[pd.DataFrame, list]: DataFrame with weather data indexed by date and list of warnings.
        """
        logger.info(
            f"Downloading Archive data for {self.start} to {self.end}, lat={self.lat}, long={self.long}"
        )
        cache_key = f"archive:{self.start.strftime('%Y%m%d')}:{self.end.strftime('%Y%m%d')}:{self.lat}:{self.long}"
        df = None
        warnings = []

        df = self._load_from_cache(cache_key, self.start, self.end)

        if df is None:
            async with ClientSession() as session:
                data, fetch_warnings = await self._fetch_data(session, self.request_url)
                warnings.extend(fetch_warnings)
                logger.debug(f"JSON returned from Archive API: {data}")
                if data and "daily" in data and "time" in data["daily"]:
                    daily_data = data["daily"]
                    expected_keys = list(self.VALID_PARAMETERS.keys())
                    missing_keys = [k for k in expected_keys if k not in daily_data]
                    if missing_keys:
                        warnings.append(f"Missing data keys: {missing_keys}")
                        logger.warning(f"Missing data keys: {missing_keys}")
                    dates = pd.to_datetime(daily_data["time"])
                    df = pd.DataFrame(
                        {
                            "date": dates,
                            "T2M_MAX": daily_data.get("temperature_2m_max", [np.nan] * len(dates)),
                            "T2M_MIN": daily_data.get("temperature_2m_min", [np.nan] * len(dates)),
                            "T2M": daily_data.get("temperature_2m_mean", [np.nan] * len(dates)),
                            "RH2M": daily_data.get("relative_humidity_2m_mean", [np.nan] * len(dates)),
                            "WS10M_MEAN": daily_data.get("windspeed_10m_mean", [np.nan] * len(dates)),
                            "ALLSKY_SFC_SW_DWN": daily_data.get("shortwave_radiation_sum", [np.nan] * len(dates)),
                            "PRECTOTCORR": daily_data.get("precipitation_sum", [np.nan] * len(dates)),
                        }
                    ).set_index("date")
                    if (
                        "shortwave_radiation_sum" in daily_data
                        and df["ALLSKY_SFC_SW_DWN"].mean() < 1
                    ):
                        warning = (
                            f"Suspiciously low ALLSKY_SFC_SW_DWN values: {df['ALLSKY_SFC_SW_DWN'].mean()} MJ/m²/day."
                        )
                        warnings.append(warning)
                        logger.warning(warning)
                    self._save_to_cache(df, cache_key)
                else:
                    warning = "No valid data available from Archive API."
                    warnings.append(warning)
                    logger.error(warning)
                    return pd.DataFrame(), warnings

        # Convert windspeed from 10m to 2m
        df["WS2M"] = df["WS10M_MEAN"].apply(lambda x: (x * 0.27778) * 0.75 if pd.notnull(x) else np.nan)

        # Filter by requested date range
        df = df[(df.index >= self.start) & (df.index <= self.end)].sort_index()

        return df, warnings

class OpenMeteoForecastAPI(BaseOpenMeteoAPI):
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast?"
    FORECAST_CACHE_EXPIRY_HOURS = 24  # 1 day

    def __init__(
        self,
        start: Union[datetime, date],
        end: Union[datetime, date],
        long: float,
        lat: float,
    ):
        """Initialize the Open-Meteo Forecast API client."""
        super().__init__(start, end, long, lat, cache_expiry_hours=self.FORECAST_CACHE_EXPIRY_HOURS)

        # Validate date range for forecast (max 14 days past data)
        period_days = (self.end - self.start).days + 1
        if period_days > 14:
            raise ValueError("Forecast API supports up to 14 days of past data.")

    def _build_request(self) -> str:
        """Build the Open-Meteo Forecast API request URL."""
        past_days = min(14, (self.end - self.start).days + 1)
        return (
            f"{self.FORECAST_URL}latitude={self.lat}&longitude={self.long}"
            f"&past_days={past_days}"
            "&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
            "relative_humidity_2m_mean,windspeed_10m_mean,shortwave_radiation_sum,precipitation_sum"
            "&format=json&models=ecmwf_ifs025"
        )

    @shared_task
    async def get_weather(self) -> Tuple[pd.DataFrame, list]:
        """
        Fetch daily weather data from Open-Meteo Forecast API.

        Returns:
            Tuple[pd.DataFrame, list]: DataFrame with weather data indexed by date and list of warnings.
        """
        logger.info(
            f"Downloading Forecast data for {self.start} to {self.end}, lat={self.lat}, long={self.long}"
        )
        cache_key = f"forecast:{self.start.strftime('%Y%m%d')}:{self.end.strftime('%Y%m%d')}:{self.lat}:{self.long}"
        df = None
        warnings = []

        df = self._load_from_cache(cache_key, self.start, self.end)

        if df is None:
            async with ClientSession() as session:
                data, fetch_warnings = await self._fetch_data(session, self.request_url)
                warnings.extend(fetch_warnings)
                logger.debug(f"JSON returned from Forecast API: {data}")
                if data and "daily" in data and "time" in data["daily"]:
                    daily_data = data["daily"]
                    expected_keys = list(self.VALID_PARAMETERS.keys())
                    missing_keys = [k for k in expected_keys if k not in daily_data]
                    if missing_keys:
                        warnings.append(f"Missing data keys: {missing_keys}")
                        logger.warning(f"Missing data keys: {missing_keys}")
                    dates = pd.to_datetime(daily_data["time"])
                    df = pd.DataFrame(
                        {
                            "date": dates,
                            "T2M_MAX": daily_data.get("temperature_2m_max", [np.nan] * len(dates)),
                            "T2M_MIN": daily_data.get("temperature_2m_min", [np.nan] * len(dates)),
                            "T2M": daily_data.get("temperature_2m_mean", [np.nan] * len(dates)),
                            "RH2M": daily_data.get("relative_humidity_2m_mean", [np.nan] * len(dates)),
                            "WS10M_MEAN": daily_data.get("windspeed_10m_mean", [np.nan] * len(dates)),
                            "ALLSKY_SFC_SW_DWN": daily_data.get("shortwave_radiation_sum", [np.nan] * len(dates)),
                            "PRECTOTCORR": daily_data.get("precipitation_sum", [np.nan] * len(dates)),
                        }
                    ).set_index("date")
                    if (
                        "shortwave_radiation_sum" in daily_data
                        and df["ALLSKY_SFC_SW_DWN"].mean() < 1
                    ):
                        warning = (
                            f"Suspiciously low ALLSKY_SFC_SW_DWN values: {df['ALLSKY_SFC_SW_DWN'].mean()} MJ/m²/day."
                        )
                        warnings.append(warning)
                        logger.warning(warning)
                    self._save_to_cache(df, cache_key)
                else:
                    warning = "No valid data available from Forecast API."
                    warnings.append(warning)
                    logger.error(warning)
                    return pd.DataFrame(), warnings

        # Convert windspeed from 10m to 2m
        df["WS2M"] = df["WS10M_MEAN"].apply(lambda x: (x * 0.27778) * 0.75 if pd.notnull(x) else np.nan)

        # Filter by requested date range
        df = df[(df.index >= self.start) & (df.index <= self.end)].sort_index()

        # Add warning for forecast data
        warnings.append("Forecast data may be less reliable due to being predictions.")

        return df, warnings