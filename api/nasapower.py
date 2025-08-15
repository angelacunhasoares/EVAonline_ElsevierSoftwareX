import asyncio
from datetime import date, datetime, timedelta
from typing import Optional, Union, Tuple
import pandas as pd
import aiohttp
from celery import shared_task
from redis import Redis
from loguru import logger  # Alterado para loguru
import pickle

# Configuração do Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

class NasaPowerAPI:
    BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point?"
    
    VALID_PARAMETERS = [
        "T2M_MAX",
        "T2M_MIN",
        "T2M",
        "RH2M",
        "WS2M",
        "ALLSKY_SFC_SW_DWN",
        "PRECTOTCORR",
    ]

    NASA_CACHE_EXPIRY_HOURS = 720  # 30 days

    def __init__(
        self,
        start: Union[date, datetime, pd.Timestamp],
        end: Union[date, datetime, pd.Timestamp],
        long: float,
        lat: float,
        parameter: Optional[list] = None,
        matopiba_only: bool = False,
    ):
        """
        Initialize the class to download daily weather data from NASA POWER.

        Args:
            start: Start date (date, datetime, or pd.Timestamp).
            end: End date (date, datetime, or pd.Timestamp).
            long: Longitude (-180 to 180).
            lat: Latitude (-90 to 90).
            parameter: List of climate parameters to download; if None, uses defaults for FAO-56 ETo.
            matopiba_only: Restrict coordinates to MATOPIBA region (default: False).

        Raises:
            ValueError: If parameters, dates, or coordinates are invalid.
        """
        if parameter is not None:
            invalid_params = [p for p in parameter if p not in self.VALID_PARAMETERS]
            if invalid_params:
                raise ValueError(
                    f"Invalid parameters: {invalid_params}. Use only {self.VALID_PARAMETERS}"
                )
        self.parameter = parameter if parameter is not None else self.VALID_PARAMETERS

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

        # Adjust end date to avoid future data
        current_date = datetime.now()
        if self.end > current_date:
            logger.warning(
                f"End date {self.end} is in the future. Adjusting to {current_date}."
            )
            self.end = current_date

        if self.end < self.start:
            raise ValueError("End date must be after start date.")

        # Validate coordinates
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90.")
        if not (-180 <= long <= 180):
            raise ValueError("Longitude must be between -180 and 180.")
        if matopiba_only and not (-14.5 <= lat <= -2.5 and -50.0 <= long <= -41.5):
            logger.warning(
                f"Coordinates (lat={lat}, long={long}) outside typical MATOPIBA range "
                "(-14.5 to -2.5 lat, -50.0 to -41.5 long). Verify if the location is valid."
            )

        self.long = long
        self.lat = lat
        self.matopiba_only = matopiba_only
        self.request = self._build_request()

        # Initialize Redis client
        try:
            self.redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
            self.redis_client.ping()  # Test connection
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    def _build_request(self) -> str:
        """Build the NASA POWER API request URL."""
        params = ",".join(self.parameter)
        start_date = self.start.strftime("%Y%m%d")
        end_date = self.end.strftime("%Y%m%d")
        return (
            f"{self.BASE_URL}parameters={params}&community=AG&longitude={self.long}"
            f"&latitude={self.lat}&start={start_date}&end={end_date}&format=JSON"
        )

    async def _fetch_data(self, session: aiohttp.ClientSession) -> Tuple[dict, list]:
        """Make an asynchronous request to the NASA POWER API."""
        warnings = []
        try:
            async with session.get(self.request, timeout=30) as response:
                response.raise_for_status()
                data = await response.json()
                if (
                    not data
                    or "properties" not in data
                    or "parameter" not in data["properties"]
                ):
                    warnings.append("Invalid response from NASA POWER API.")
                    logger.error(warnings[-1])
                    return {}, warnings
                return data, warnings
        except aiohttp.ClientResponseError as e:
            warnings.append(f"HTTP error downloading NASA POWER data: {e.status} - {e.message}")
            logger.error(warnings[-1])
            return {}, warnings
        except asyncio.TimeoutError:
            warnings.append(f"Timeout downloading NASA POWER data for {self.request}")
            logger.error(warnings[-1])
            return {}, warnings
        except Exception as e:
            warnings.append(f"Unexpected error downloading NASA POWER data: {e}")
            logger.error(warnings[-1])
            return {}, warnings

    def _save_to_cache(self, df: pd.DataFrame, cache_key: str) -> None:
        """Save data to Redis cache."""
        if not self.redis_client:
            logger.warning("No Redis connection. Skipping cache save.")
            return
        try:
            self.redis_client.setex(
                cache_key,
                timedelta(hours=self.NASA_CACHE_EXPIRY_HOURS),
                pickle.dumps(df)
            )
            logger.info(f"Saved to Redis cache: {cache_key}")
        except Exception as e:
            logger.error(f"Failed to save to Redis cache: {e}")

    def _load_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Load data from Redis cache if available and valid."""
        if not self.redis_client:
            logger.warning("No Redis connection. Skipping cache load.")
            return None
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                df = pickle.loads(cached_data)
                if df.index.min() <= self.start and df.index.max() >= self.end:
                    logger.info(f"Loaded from Redis cache: {cache_key}")
                    return df
                else:
                    logger.info(f"Redis cached data does not cover requested range: {cache_key}")
            else:
                logger.info(f"Redis cache not found: {cache_key}")
        except Exception as e:
            logger.error(f"Failed to load from Redis cache: {e}")
        return None

    @shared_task
    async def get_weather(self) -> Tuple[pd.DataFrame, list]:
        """
        Download daily weather data from NASA POWER asynchronously.

        Returns:
            Tuple[pd.DataFrame, list]: DataFrame with daily climate parameters indexed by date and list of warnings.

        Example:
            >>> nasa = NasaPowerAPI(start="2023-01-01", end="2023-01-07", long=-45.0, lat=-10.0)
            >>> df, warnings = await nasa.get_weather()
        """
        logger.info(
            f"Downloading data for {self.start} to {self.end}, lat={self.lat}, long={self.long}"
        )
        cache_key = f"nasa_power:{self.start.strftime('%Y%m%d')}:{self.end.strftime('%Y%m%d')}:{self.lat}:{self.long}"
        df = None
        warnings = []

        df = self._load_from_cache(cache_key)

        if df is None:
            async with aiohttp.ClientSession() as session:
                data, fetch_warnings = await self._fetch_data(session)
                warnings.extend(fetch_warnings)
                if data and "properties" in data and "parameter" in data["properties"]:
                    params = data["properties"]["parameter"]
                    weather_df = pd.DataFrame(params)
                    weather_df.index = pd.to_datetime(
                        weather_df.index, format="%Y%m%d", errors="coerce"
                    )
                    weather_df = weather_df[weather_df.index.notna()]
                    weather_df = weather_df.loc[self.start:self.end].dropna(how="all")
                    weather_df = weather_df[self.parameter]

                    self._save_to_cache(weather_df, cache_key)
                    df = weather_df
                else:
                    logger.error(f"Invalid or empty API response for {self.request}")
                    warnings.append("No valid data available from NASA POWER API.")
                    return pd.DataFrame(), warnings

        if df is None or df.empty:
            logger.error(
                f"Failed to retrieve NASA POWER data for lat={self.lat}, lng={self.long} between {self.start} and {self.end}"
            )
            warnings.append("Failed to retrieve NASA POWER data.")
            return pd.DataFrame(), warnings

        return df, warnings