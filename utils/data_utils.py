import logging
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
import redis
import pickle
from celery import shared_task
from utils.get_translations import get_translations

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_EXPIRY_HOURS = 24  # 24 hours


@shared_task
def load_matopiba_data(lang: str = "pt") -> Tuple[pd.DataFrame, list]:
    """
    Load the MATOPIBA cities DataFrame from CSV, with caching in Redis.

    Args:
        lang (str): Language code ('pt' for Portuguese, 'en' for English).

    Returns:
        Tuple[pd.DataFrame, list]: DataFrame with MATOPIBA cities and list of warnings.

    Example:
        >>> df, warnings = load_matopiba_data("en")
        >>> print(df.head(), warnings)
    """
    t = get_translations(lang)
    warnings = []
    cache_key = "matopiba_cities"

    # Initialize Redis client
    redis_client = None
    try:
        redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        cached_data = redis_client.get(cache_key)
        if cached_data:
            df = pickle.loads(cached_data)
            logger.info("Loaded MATOPIBA DataFrame from Redis cache")
            return df, [t["loaded_from_cache"]]
    except redis.RedisError as e:
        warnings.append(t["redis_error"].format(str(e)))
        logger.error(warnings[-1])

    # Load CSV
    try:
        base_dir = Path(os.getenv("DATA_DIR", Path(__file__).parent.parent / "data"))
        csv_path = base_dir / "CITIES_MATOPIBA_337.csv"
        if not csv_path.exists():
            raise FileNotFoundError(t["csv_not_found"].format(csv_path))

        df = pd.read_csv(csv_path)
        state_codes = {
            "BA": "Bahia",
            "PI": "Piauí",
            "MA": "Maranhão",
            "TO": "Tocantins",
        }
        df["UF"] = df["UF"].astype(str).str[:2].map(state_codes)
        df = df.dropna(subset=["UF", "LATITUDE", "LONGITUDE", "HEIGHT"])
        logger.info("MATOPIBA DataFrame loaded successfully")

        # Validate data
        if df.empty:
            warnings.append(t["empty_dataframe"])
            logger.error(warnings[-1])
            return df, warnings

        # Save to cache
        if redis_client:
            try:
                redis_client.setex(cache_key, timedelta(hours=CACHE_EXPIRY_HOURS), pickle.dumps(df))
                logger.info("Saved MATOPIBA DataFrame to Redis cache")
            except redis.RedisError as e:
                warnings.append(t["redis_save_error"].format(str(e)))
                logger.error(warnings[-1])

        return df, warnings

    except FileNotFoundError as e:
        warnings.append(str(e))
        logger.error(warnings[-1])
        return pd.DataFrame(), warnings
    except Exception as e:
        warnings.append(t["load_error"].format(str(e)))
        logger.error(warnings[-1])
        return pd.DataFrame(), warnings


def build_input_data(
    mode: str,
    database: Optional[str],
    data_inicial: Optional[str],
    data_final: Optional[str],
    lat: Optional[float],
    lng: Optional[float],
    elevation: Optional[float],
    estado: Optional[str] = None,
    cidade: Optional[str] = None,
    lang: str = "pt"
) -> Tuple[Dict[str, Optional[object]], list]:
    """
    Build the input data dictionary based on the calculation mode.

    Args:
        mode (str): Calculation mode ("Global" or "MATOPIBA").
        database (Optional[str]): Selected database (e.g., "NASA POWER").
        data_inicial (Optional[str]): Start date (DD/MM/YYYY).
        data_final (Optional[str]): End date (DD/MM/YYYY).
        lat (Optional[float]): Latitude.
        lng (Optional[float]): Longitude.
        elevation (Optional[float]): Elevation in meters.
        estado (Optional[str]): State for MATOPIBA mode.
        cidade (Optional[str]): City for MATOPIBA mode.
        lang (str): Language code ('pt' for Portuguese, 'en' for English).

    Returns:
        Tuple[Dict[str, Optional[object]], list]: Input data dictionary and list of warnings.

    Example:
        >>> input_data, warnings = build_input_data(
        ...     mode="Global", database="NASA POWER", data_inicial="01/01/2023",
        ...     data_final="07/01/2023", lat=-10.0, lng=-45.0, elevation=500.0, lang="en"
        ... )
    """
    t = get_translations(lang)
    warnings = []
    input_data = {
        "mode": mode,
        "database": database,
        "data_inicial": data_inicial,
        "data_final": data_final
    }

    # Validate mode
    if mode not in ["Global", "MATOPIBA"]:
        warnings.append(t["invalid_mode"].format(mode))
        logger.error(warnings[-1])
        return input_data, warnings

    # Validate common parameters
    hoje = date.today()
    um_ano_atras = hoje - timedelta(days=365)
    limite_futuro = hoje + timedelta(days=2)

    if not database or database == t["choose_database"]:
        warnings.append(t["no_database_selected"])
        logger.error(warnings[-1])
    if not data_inicial or not data_final:
        warnings.append(t["no_dates_selected"])
        logger.error(warnings[-1])
    else:
        try:
            data_inicial_dt = pd.to_datetime(data_inicial, format="%d/%m/%Y")
            data_final_dt = pd.to_datetime(data_final, format="%d/%m/%Y")
            delta = (data_final_dt - data_inicial_dt).days + 1
            if data_final_dt < data_inicial_dt:
                warnings.append(t["invalid_date_range"])
                logger.error(warnings[-1])
            elif not (7 <= delta <= 15):
                warnings.append(t["invalid_period"].format(delta))
                logger.error(warnings[-1])
            elif data_inicial_dt < um_ano_atras:
                warnings.append(t["date_too_old"].format(um_ano_atras.strftime("%d/%m/%Y")))
                logger.error(warnings[-1])
            elif data_final_dt > limite_futuro:
                warnings.append(t["date_too_future"].format(limite_futuro.strftime("%d/%m/%Y")))
                logger.error(warnings[-1])
        except ValueError as e:
            warnings.append(t["invalid_date_format"].format(str(e)))
            logger.error(warnings[-1])

    # Mode-specific parameters
    if mode == "Global":
        if lat is None or lng is None:
            warnings.append(t["no_coords_global"])
            logger.error(warnings[-1])
        input_data.update({"latitude": lat, "longitude": lng, "elevation": elevation})
    elif mode == "MATOPIBA":
        if cidade and estado:
            df_matopiba, matopiba_warnings = load_matopiba_data(lang)
            warnings.extend(matopiba_warnings)
            if not df_matopiba.empty:
                city_match = df_matopiba[(df_matopiba["UF"] == estado) & (df_matopiba["CITY"] == cidade)]
                if city_match.empty:
                    warnings.append(t["no_matching_city"].format(cidade, estado))
                    logger.error(warnings[-1])
                else:
                    input_data.update({
                        "estado": estado,
                        "cidade": cidade,
                        "latitude": city_match["LATITUDE"].iloc[0],
                        "longitude": city_match["LONGITUDE"].iloc[0],
                        "elevation": city_match["HEIGHT"].iloc[0]
                    })
        elif lat is None or lng is None:
            warnings.append(t["no_coords_matopiba"])
            logger.error(warnings[-1])
        else:
            input_data.update({"latitude": lat, "longitude": lng, "elevation": elevation})

    return input_data, warnings