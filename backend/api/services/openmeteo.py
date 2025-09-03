import os
import pickle
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Union

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


class OpenMeteoForecastAPI(OpenMeteoAPI):
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast?"
    FORECAST_CACHE_EXPIRY_HOURS = 24  # 1 day

    # Parameter ranges for validation (hourly parameters)
    VALID_PARAMETERS = {
        "temperature_2m": (-100, 100),  # °C
        "relative_humidity_2m": (0, 100),  # %
        "et0_fao_evapotranspiration": (0, 50),  # mm
        "wind_speed_10m": (0, 100),  # m/s
        "shortwave_radiation": (0, 1500),  # W/m²
        "precipitation_probability": (0, 100)  # %
    }

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
            "&hourly=temperature_2m,relative_humidity_2m,"
            "et0_fao_evapotranspiration,wind_speed_10m,"
            "shortwave_radiation,precipitation_probability"
            "&format=json&models=best_match"
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
        url = self._build_request()
        data, fetch_warnings = self._fetch_data(url)
        warnings.extend(fetch_warnings)
        logger.debug("Dados da API Forecast: %s", data)
        
        # Valida resposta
        if not (data and "hourly" in data and "time" in data["hourly"]):
            msg = "Resposta inválida da API Forecast"
            logger.error(msg)
            warnings.append(msg)
            return pd.DataFrame(), warnings
            
        hourly_data = data["hourly"]
        expected_keys = list(self.VALID_PARAMETERS.keys())
        missing_keys = [k for k in expected_keys if k not in hourly_data]
        if missing_keys:
            msg = f"Campos ausentes: {missing_keys}"
            warnings.append(msg)
            logger.warning(msg)

        try:
            # Converte datas para datetime
            dates = pd.to_datetime(hourly_data["time"])
            len_dates = len(dates)
            na_array = [np.nan] * len_dates
            
            # Cria DataFrame com dados disponíveis
            df = pd.DataFrame({
                "date": dates,
                "T2M": hourly_data.get(
                    "temperature_2m", na_array
                ),
                "RH2M": hourly_data.get(
                    "relative_humidity_2m", na_array
                ),
                "ETO": hourly_data.get(
                    "et0_fao_evapotranspiration", na_array
                ),
                "WS10M": hourly_data.get(
                    "wind_speed_10m", na_array
                ),
                "ALLSKY_SFC_SW_DWN": hourly_data.get(
                    "shortwave_radiation", na_array
                ),
                "PRECIP_PROB": hourly_data.get(
                    "precipitation_probability", na_array
                )
            }).set_index("date")
            
            # Valida dados de radiação
            if (
                "shortwave_radiation" in hourly_data and
                df["ALLSKY_SFC_SW_DWN"].mean() < 1
            ):
                msg = (
                    "Valores baixos de radiação solar: "
                    f"{df['ALLSKY_SFC_SW_DWN'].mean():.1f} W/m²"
                )
                warnings.append(msg)
                logger.warning(msg)
            
            # Ajusta velocidade do vento (converte m/s para km/h)
            def adjust_wind(ws: float) -> float:
                if pd.isna(ws):
                    return np.nan
                # Converte m/s para km/h
                return ws * 3.6
                
            df["WS2M"] = df["WS10M"].apply(adjust_wind)
            df = df.drop(columns=["WS10M"])

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
