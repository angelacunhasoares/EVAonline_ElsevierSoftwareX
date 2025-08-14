import asyncio
import logging
import os
from datetime import date, datetime, timedelta
from typing import Optional, Union, Tuple
import pandas as pd
import aiohttp
from celery import shared_task
import redis
import pickle
from glob import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Redis configuration (for Render)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

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

    CACHE_DIR = os.path.join(os.path.dirname(__file__), "nasa_power_cache")
    MAX_CACHE_SIZE_MB = 500
    NASA_CACHE_EXPIRY_HOURS = 720  # 30 days

    def __init__(
        self,
        start: Union[date, datetime, pd.Timestamp],
        end: Union[date, datetime, pd.Timestamp],
        long: float,
        lat: float,
        parameter: Optional[list] = None,
        use_cache: bool = True,
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
            use_cache: Whether to use Redis cache (default: True).
            matopiba_only: Restrict coordinates to MATOPIBA region (default: False).

        Returns:
            None

        Example:
            >>> nasa = NasaPowerAPI(
            ...     start="2023-01-01",
            ...     end="2023-01-07",
            ...     long=-45.0,
            ...     lat=-10.0
            ... )
            >>> df = await nasa.get_weather()
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
        self.use_cache = use_cache
        self.matopiba_only = matopiba_only
        self.request = self._build_request()

        # Initialize Redis client
        try:
            self.redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            self.redis_client.ping()  # Test connection
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}. Falling back to file cache.")
            self.use_cache = False
            self.redis_client = None

        # Create file cache directory if needed
        if not self.use_cache and not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR)

    def _manage_cache_size(self) -> None:
        """Manage file cache size, removing outdated or oldest files if necessary."""
        if not self.use_cache or self.redis_client:
            return

        cache_files = glob(os.path.join(self.CACHE_DIR, "*.pkl"))
        total_size = sum(os.path.getsize(f) for f in cache_files) / (1024 * 1024)  # Size in MB
        expiry_time = datetime.now() - timedelta(hours=self.NASA_CACHE_EXPIRY_HOURS)

        # Remove outdated files first
        for f in cache_files:
            cache_mtime = datetime.fromtimestamp(os.path.getmtime(f))
            if cache_mtime < expiry_time:
                file_size = os.path.getsize(f) / (1024 * 1024)
                os.remove(f)
                total_size -= file_size
                logger.info(f"Removed outdated cache file: {f}")

        # Remove oldest files if still over limit
        if total_size > self.MAX_CACHE_SIZE_MB:
            cache_files = glob(os.path.join(self.CACHE_DIR, "*.pkl"))
            cache_files.sort(key=os.path.getmtime)
            while total_size > self.MAX_CACHE_SIZE_MB and cache_files:
                oldest_file = cache_files.pop(0)
                file_size = os.path.getsize(oldest_file) / (1024 * 1024)
                os.remove(oldest_file)
                total_size -= file_size
                logger.info(f"Removed oldest cache file: {oldest_file}")

    def _build_request(self) -> str:
        """Build the NASA POWER API request URL."""
        params = ",".join(self.parameter)
        start_date = self.start.strftime("%Y%m%d")
        end_date = self.end.strftime("%Y%m%d")
        return (
            f"{self.BASE_URL}parameters={params}&community=AG&longitude={self.long}"
            f"&latitude={self.lat}&start={start_date}&end={end_date}&format=JSON"
        )

    async def _fetch_data(self, session: aiohttp.ClientSession) -> dict:
        """Make an asynchronous request to the NASA POWER API."""
        try:
            async with session.get(self.request, timeout=30) as response:
                response.raise_for_status()
                data = await response.json()
                if (
                    not data
                    or "properties" not in data
                    or "parameter" not in data["properties"]
                ):
                    raise ValueError("Invalid response from NASA POWER API.")
                return data
        except aiohttp.ClientResponseError as e:
            logger.error(
                f"HTTP error downloading NASA POWER data: {e.status} - {e.message}"
            )
            return {}
        except asyncio.TimeoutError:
            logger.error(f"Timeout downloading NASA POWER data for {self.request}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error downloading NASA POWER data: {e}")
            return {}

    def _is_cache_outdated(self, cache_key: str) -> bool:
        """Check if cache is outdated (Redis or file)."""
        if not self.use_cache:
            return True

        if self.redis_client:
            cache_mtime = self.redis_client.get(f"{cache_key}:mtime")
            if not cache_mtime:
                logger.info(f"Redis cache not found: {cache_key}")
                return True
            cache_mtime = datetime.fromtimestamp(float(cache_mtime))
            expiry_time = datetime.now() - timedelta(hours=self.NASA_CACHE_EXPIRY_HOURS)
            if cache_mtime < expiry_time:
                logger.info(
                    f"Redis cache outdated: {cache_key}, mtime={cache_mtime}, expiry_time={expiry_time}"
                )
                return True
            logger.info(f"Redis cache valid: {cache_key}, mtime={cache_mtime}")
            return False
        else:
            cache_path = os.path.join(self.CACHE_DIR, f"{cache_key}.pkl")
            if not os.path.exists(cache_path):
                logger.info(f"File cache not found: {cache_path}")
                return True
            cache_mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
            expiry_time = datetime.now() - timedelta(hours=self.NASA_CACHE_EXPIRY_HOURS)
            if cache_mtime < expiry_time:
                logger.info(
                    f"File cache outdated: {cache_path}, mtime={cache_mtime}, expiry_time={expiry_time}"
                )
                return True
            logger.info(f"File cache valid: {cache_path}, mtime={cache_mtime}")
            return False

    def _save_to_cache(self, df: pd.DataFrame, cache_key: str) -> None:
        """Save data to Redis or file cache."""
        if not self.use_cache:
            return

        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key,
                    timedelta(hours=self.NASA_CACHE_EXPIRY_HOURS),
                    pickle.dumps(df)
                )
                self.redis_client.setex(
                    f"{cache_key}:mtime",
                    timedelta(hours=self.NASA_CACHE_EXPIRY_HOURS),
                    datetime.now().timestamp()
                )
                logger.info(f"Saved to Redis cache: {cache_key}")
            except redis.RedisError as e:
                logger.error(f"Failed to save to Redis cache: {e}")
        else:
            cache_path = os.path.join(self.CACHE_DIR, f"{cache_key}.pkl")
            with open(cache_path, "wb") as f:
                pickle.dump(df, f)
            logger.info(f"Saved to file cache: {cache_path}")

    def _load_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Load data from Redis or file cache if available and valid."""
        if not self.use_cache:
            return None

        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    df = pickle.loads(cached_data)
                    if df.index.min() <= self.start and df.index.max() >= self.end:
                        logger.info(f"Loaded from Redis cache: {cache_key}")
                        return df
                    else:
                        logger.info(
                            f"Redis cached data does not cover requested range: {cache_key}"
                        )
            except redis.RedisError as e:
                logger.error(f"Failed to load from Redis cache: {e}")
        else:
            cache_path = os.path.join(self.CACHE_DIR, f"{cache_key}.pkl")
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, "rb") as f:
                        df = pickle.load(f)
                        if df.index.min() <= self.start and df.index.max() >= self.end:
                            logger.info(f"Loaded from file cache: {cache_path}")
                            return df
                        else:
                            logger.info(
                                f"File cached data does not cover requested range: {cache_path}"
                            )
                except Exception as e:
                    logger.error(f"Error loading file cache {cache_path}: {e}")
        return None

    @shared_task
    async def get_weather(self) -> Optional[pd.DataFrame]:
        """
        Download daily weather data from NASA POWER asynchronously.

        Returns:
            pd.DataFrame: DataFrame with daily climate parameters indexed by date, or None if failed.

        Example:
            >>> nasa = NasaPowerAPI(start="2023-01-01", end="2023-01-07", long=-45.0, lat=-10.0)
            >>> df = await nasa.get_weather()
        """
        logger.info(
            f"Downloading data for {self.start} to {self.end}, lat={self.lat}, long={self.long}"
        )
        cache_key = f"nasa_power_{self.start.strftime('%Y%m%d')}_{self.end.strftime('%Y%m%d')}_{self.lat}_{self.long}"
        df = None

        if self.use_cache:
            df = self._load_from_cache(cache_key)

        if df is None or (self.use_cache and self._is_cache_outdated(cache_key)):
            async with aiohttp.ClientSession() as session:
                data = await self._fetch_data(session)
                if data and "properties" in data and "parameter" in data["properties"]:
                    params = data["properties"]["parameter"]
                    weather_df = pd.DataFrame(params)
                    weather_df.index = pd.to_datetime(
                        weather_df.index, format="%Y%m%d", errors="coerce"
                    )
                    weather_df = weather_df[weather_df.index.notna()]
                    weather_df = weather_df.loc[self.start:self.end].dropna(how="all")
                    weather_df = weather_df[self.parameter]

                    if self.use_cache:
                        self._save_to_cache(weather_df, cache_key)
                    df = weather_df
                else:
                    logger.error(f"Invalid or empty API response for {self.request}")
                    return None

        if df is None:
            logger.error(
                f"Failed to retrieve NASA POWER data for lat={self.lat}, lng={self.long} between {self.start} and {self.end}"
            )
            return None

        return df