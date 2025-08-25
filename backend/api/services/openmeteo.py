"""OpenMeteo API clients for weather data.

This module provides synchronous clients for OpenMeteo APIs:
- OpenMeteoArchiveAPI for historical weather data
- OpenMeteoForecastAPI for weather forecasts (upcoming)

The clients support:
- Data validation and type checking
- Redis caching with configurable expiry
- Proper error handling and logging

Example:
    >>> from api.openmeteo import OpenMeteoArchiveAPI
    >>> client = OpenMeteoArchiveAPI(
    ...     start='2024-01-01',
    ...     end='2024-01-07',
    ...     lat=-22.7,
    ...     long=-47.6
    ... )
    >>> df, warnings = client.get_weather_sync()
    >>> print(df.head())

See README.md for architecture and design decisions.
"""

from datetime import date, datetime, timedelta
import os
import pickle
from typing import List, Optional, Tuple, Union

# Define the base class for OpenMeteo APIs
class OpenMeteoAPI:
    """Base class for OpenMeteo API clients."""
    
    def __init__(self):
        pass

import numpy as np
import pandas as pd
import requests
from celery import shared_task
from loguru import logger
from redis import Redis
from requests.exceptions import RequestException

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


class OpenMeteoAPI:
    """Base class for OpenMeteo API clients.

    Provides common functionality for OpenMeteo Archive and Forecast APIs including
    coordinate validation, caching, data validation, and request handling.

    Attributes:
        start (datetime): Start date for weather data.
        end (datetime): End date for weather data.
        lat (float): Latitude (-90 to 90).
        long (float): Longitude (-180 to 180).
        cache_expiry_hours (int): Cache expiry time in hours.

    Raises:
        ValueError: If coordinates are invalid or dates are incorrect.
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
        """
        # Convert dates to datetime if needed
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

        # Validate coordinates
        if not (-90 <= lat <= 90):
            msg = "Latitude must be between -90 and 90 degrees"
            raise ValueError(msg)

        if not (-180 <= long <= 180):
            msg = "Longitude must be between -180 and 180 degrees"
            raise ValueError(msg)

        # Store instance attributes
        self.long = long
        self.lat = lat
        self.cache_expiry_hours = cache_expiry_hours

        # Initialize Redis connection
        try:
            self.redis_client = Redis.from_url(
                REDIS_URL, decode_responses=False
            )
            self.redis_client.ping()
        except Exception as e:
            logger.error("Failed to connect to Redis: %s", e)
            self.redis_client = None

    def _fetch_data(self, url: str) -> Tuple[dict, List[str]]:
        """Make a synchronous request to the OpenMeteo API.

        Args:
            url: Complete URL with all parameters.

        Returns:
            Tuple[dict, List[str]]: API response data and warnings.
        """
        warnings = []
        try:
            response = requests.get(url, timeout=10)
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
        msg = "build_url() must be implemented by subclasses"
        raise NotImplementedError(msg)

    def _save_to_cache(
        self, df: pd.DataFrame, cache_key: str
    ) -> None:
        """Save DataFrame to Redis cache.

        Args:
            df: DataFrame to save.
            cache_key: Redis key to use.
        """
        if not self.redis_client:
            return

        try:
            cached_data = pickle.dumps(df)
            self.redis_client.setex(
                cache_key,
                timedelta(hours=self.cache_expiry_hours),
                cached_data
            )
            logger.info("Data saved to cache: %s", cache_key)

        except Exception as e:
            logger.error("Failed to save to cache: %s", e)

    def _load_from_cache(
        self,
        cache_key: str,
        start: datetime,
        end: datetime
    ) -> Optional[pd.DataFrame]:
        """Load DataFrame from Redis cache.

        Args:
            cache_key: Redis key to load.
            start: Start date to filter.
            end: End date to filter.

        Returns:
            DataFrame if found and valid, None otherwise.
        """
        if not self.redis_client:
            return None

        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data is None:
                return None

            df = pickle.loads(cached_data)
            logger.info("Data loaded from cache: %s", cache_key)

            # Filter to requested date range
            return df[
                (df.index >= start) & (df.index <= end)
            ].sort_index()

        except Exception as e:
            logger.error("Failed to load from cache: %s", e)
            return None


class OpenMeteoArchiveAPI(OpenMeteoAPI):
    """OpenMeteo Archive API client.

    Retrieves historical weather data for a given location and time period.
    Supports caching and data validation.

    Attributes:
        ARCHIVE_URL (str): Base URL for Archive API.
        ARCHIVE_CACHE_EXPIRY_HOURS (int): Cache expiry time.
        VALID_PARAMETERS (Dict[str, Tuple[float, float]]): Valid ranges.
    """

    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive?"
    ARCHIVE_CACHE_EXPIRY_HOURS = 168  # 1 week

    # Parameter ranges for validation
    VALID_PARAMETERS = {
        "temperature_2m_max": (-100, 100),  # °C
        "temperature_2m_min": (-100, 100),  # °C
        "temperature_2m_mean": (-100, 100),  # °C
        "relative_humidity_2m_mean": (0, 100),  # %
        "windspeed_10m_mean": (0, 100),  # m/s
        "shortwave_radiation_sum": (0, 50),  # MJ/m²/dia
        "precipitation_sum": (0, 1000)  # mm
    }

    def __init__(
        self,
        start: Union[datetime, date],
        end: Union[datetime, date],
        lat: float,
        long: float
    ) -> None:
        """Initialize OpenMeteo Archive API client.

        Args:
            start: Start date.
            end: End date.
            lat: Latitude (-90 to 90).
            long: Longitude (-180 to 180).
        """
        # Validate current date constraints
        current_date = datetime.now()
        tomorrow = current_date + timedelta(days=1)
        one_year_ago = current_date - timedelta(days=365)

        if isinstance(start, date):
            start = datetime.combine(start, datetime.min.time())
        if isinstance(end, date):
            end = datetime.combine(end, datetime.min.time())

        if start < one_year_ago:
            msg = "Start date cannot be more than 1 year ago"
            raise ValueError(msg)
            
        if end > tomorrow:
            logger.warning(
                "End date %s is in the future. Adjusting to %s",
                end, tomorrow
            )
            end = tomorrow

        # Validate period range (7-15 days)
        period_days = (end - start).days + 1
        if not 7 <= period_days <= 15:
            msg = "Period must be between 7 and 15 days"
            raise ValueError(msg)

        # Initialize base class
        super().__init__(
            start=start,
            end=end,
            lat=lat,
            long=long,
            cache_expiry_hours=self.ARCHIVE_CACHE_EXPIRY_HOURS
        )

    def build_url(self) -> str:
        """Build the Archive API request URL.

        Returns:
            Complete URL for API request.
        """
        # List the daily parameters we want
        daily_params = [
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "relative_humidity_2m_mean",
            "windspeed_10m_mean", 
            "shortwave_radiation_sum",
            "precipitation_sum"
        ]

        # Build URL with parameters
        url = (
            f"{self.ARCHIVE_URL}latitude={self.lat}&longitude={self.long}"
            f"&start_date={self.start:%Y-%m-%d}&end_date={self.end:%Y-%m-%d}"
            f"&daily={','.join(daily_params)}&format=json&models=ecmwf_ifs025"
        )

        return url

    @shared_task
    def get_weather_sync(self) -> Tuple[pd.DataFrame, List[str]]:
        """Download weather data from OpenMeteo Archive API.

        Returns:
            Tuple[pd.DataFrame, List[str]]: Weather data and warnings.
        """
        logger.info(
            "Downloading Archive data for %s to %s (lat=%s, long=%s)",
            self.start.strftime("%Y-%m-%d"),
            self.end.strftime("%Y-%m-%d"),
            self.lat,
            self.long
        )

        # Generate cache key
        cache_key = (
            f"archive:{self.start:%Y%m%d}:"
            f"{self.end:%Y%m%d}:{self.lat}:{self.long}"
        )
        warnings = []

        # Try loading from cache first
        df = self._load_from_cache(cache_key, self.start, self.end)
        if df is not None:
            return df, warnings

        # Get request URL and fetch data
        url = self.build_url()
        data, fetch_warnings = self._fetch_data(url)
        warnings.extend(fetch_warnings)
        logger.debug("Archive API response: %s", data)

        # Validate response structure
        if not (data and "daily" in data and "time" in data["daily"]):
            msg = "Invalid response from Archive API"
            logger.error(msg)
            warnings.append(msg)
            return pd.DataFrame(), warnings

        daily_data = data["daily"]
        expected_keys = list(self.VALID_PARAMETERS.keys())
        missing_keys = [k for k in expected_keys if k not in daily_data]
        if missing_keys:
            msg = f"Missing data fields: {missing_keys}"
            warnings.append(msg)
            logger.warning(msg)

        try:
            # Convert dates and create DataFrame
            dates = pd.to_datetime(daily_data["time"])
            len_dates = len(dates)
            na_array = [np.nan] * len_dates
            
            df = pd.DataFrame({
                "date": dates,
                "T2M_MAX": daily_data.get(
                    "temperature_2m_max", na_array
                ),
                "T2M_MIN": daily_data.get(
                    "temperature_2m_min", na_array
                ),
                "T2M": daily_data.get(
                    "temperature_2m_mean", na_array
                ),
                "RH2M": daily_data.get(
                    "relative_humidity_2m_mean",
                    na_array
                ),
                "WS10M_MEAN": daily_data.get(
                    "windspeed_10m_mean",
                    na_array
                ),
                "ALLSKY_SFC_SW_DWN": daily_data.get(
                    "shortwave_radiation_sum",
                    na_array
                ),
                "PRECTOTCORR": daily_data.get(
                    "precipitation_sum",
                    na_array
                )
            }).set_index("date")

            # Convert wind speed
            def adjust_wind(ws: float) -> float:
                if pd.isna(ws):
                    return np.nan
                # Convert m/s to km/h and adjust for height
                return (ws * 3.6) * 0.75

            df["WS2M"] = df["WS10M_MEAN"].apply(adjust_wind)
            df = df.drop(columns=["WS10M_MEAN"])

            # Filter to requested date range
            df = df[
                (df.index >= self.start) &
                (df.index <= self.end)
            ].sort_index()

            # Save to cache and return
            self._save_to_cache(df, cache_key)
            return df, warnings

        except Exception as e:
            msg = f"Error processing Archive API data: {e}"
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
    cache_expiry_hours = 24 # 24 hours

    # Initialize Redis client
    try:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
    except Exception as e:
        msg = f"Failed to connect to Redis: {e}"
        logger.error(msg)
        warnings.append(msg)
        return 0.0, warnings

    # Check cache
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            elevation = float(cached_data)
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

    # Get elevation from API
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

        # Save to cache
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
class OpenMeteoForecastAPI(OpenMeteoAPI):
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
    def get_weather_sync(self) -> Tuple[pd.DataFrame, List[str]]:
        """
        Busca dados meteorológicos da API Open-Meteo Forecast.

        Returns:
            Tuple[pd.DataFrame, List[str]]: DataFrame com dados e avisos.
        """
        logger.info(
            "Baixando dados Forecast de %s a %s (lat=%s, long=%s)",
            self.start.strftime("%Y-%m-%d"),
            self.end.strftime("%Y-%m-%d"),
            self.lat,
            self.long
        )
        
        # Gera chave de cache
        # Gera chave de cache
        cache_key = (
            f"forecast:{self.start:%Y%m%d}:"
            f"{self.end:%Y%m%d}:{self.lat}:{self.long}"
        )
        warnings = []

        # Tenta carregar do cache
        df = self._load_from_cache(cache_key, self.start, self.end)
        if df is not None:
            return df, warnings

        # Busca dados da API
        data, fetch_warnings = self._fetch_data(self.request_url)
        warnings.extend(fetch_warnings)
        logger.debug("Dados da API Forecast: %s", data)
        
        # Valida resposta
        if not (data and "daily" in data and "time" in data["daily"]):
            msg = "Resposta inválida da API Forecast"
            logger.error(msg)
            warnings.append(msg)
            return pd.DataFrame(), warnings
            
        daily_data = data["daily"]
        expected_keys = list(self.VALID_PARAMETERS.keys())
        missing_keys = [k for k in expected_keys if k not in daily_data]
        if missing_keys:
            msg = f"Campos ausentes: {missing_keys}"
            warnings.append(msg)
            logger.warning(msg)

        try:
            # Converte datas para datetime
            dates = pd.to_datetime(daily_data["time"])
            len_dates = len(dates)
            na_array = [np.nan] * len_dates
            
            # Cria DataFrame com dados disponíveis
            df = pd.DataFrame({
                "date": dates,
                "T2M_MAX": daily_data.get(
                    "temperature_2m_max", na_array
                ),
                "T2M_MIN": daily_data.get(
                    "temperature_2m_min", na_array
                ),
                "T2M": daily_data.get(
                    "temperature_2m_mean", na_array
                ),
                "RH2M": daily_data.get(
                    "relative_humidity_2m_mean",
                    na_array
                ),
                "WS10M_MEAN": daily_data.get(
                    "windspeed_10m_mean",
                    na_array
                ),
                "ALLSKY_SFC_SW_DWN": daily_data.get(
                    "shortwave_radiation_sum",
                    na_array
                ),
                "PRECTOTCORR": daily_data.get(
                    "precipitation_sum",
                    na_array
                )
            }).set_index("date")
            
            # Valida dados de radiação
            if (
                "shortwave_radiation_sum" in daily_data and
                df["ALLSKY_SFC_SW_DWN"].mean() < 1
            ):
                msg = (
                    "Valores baixos de radiação solar: "
                    f"{df['ALLSKY_SFC_SW_DWN'].mean():.1f} MJ/m²/dia"
                )
                warnings.append(msg)
                logger.warning(msg)
            
            # Ajusta velocidade do vento
            def adjust_wind(ws: float) -> float:
                if pd.isna(ws):
                    return np.nan
                # Converte m/s para km/h e ajusta altura
                return (ws * 3.6) * 0.75
                
            df["WS2M"] = df["WS10M_MEAN"].apply(adjust_wind)
            df = df.drop(columns=["WS10M_MEAN"])

            # Filtra período
            df = df[
                (df.index >= self.start) &
                (df.index <= self.end)
            ].sort_index()
            
            # Salva no cache
            self._save_to_cache(df, cache_key)

            warnings.append(
                "Os dados de previsão podem ser menos confiáveis por serem "
                "projeções."
            )
            return df, warnings

        except Exception as e:
            msg = f"Erro ao processar dados Forecast: {e}"
            logger.error(msg)
            warnings.append(msg)
            return pd.DataFrame(), warnings

        # Just remove this redundant section
        pass
        df = df[(df.index >= self.start) & (df.index <= self.end)].sort_index()

        # Add warning for forecast data
        warnings.append("Forecast data may be less reliable due to being predictions.")

        return df, warnings