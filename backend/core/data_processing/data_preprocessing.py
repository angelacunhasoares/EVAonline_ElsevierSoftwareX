import os
from datetime import timedelta
import numpy as np
import pandas as pd
import redis
import pickle
from celery import shared_task
from loguru import logger
from typing import Tuple, Optional, List

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_EXPIRY_HOURS = 24  # 24 hours

# Configure logging (already configured in eto_calculator.py, so no need to add again here)


@shared_task
def data_initial_validate(weather_df: pd.DataFrame, latitude: float) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validates weather data based on physical limits from Xavier et al. (2016), Xavier et al. (2022) and replaces
    out-of-range values with NaN.

    Args:
        weather_df (pd.DataFrame): Weather data with index as datetime and columns T2M_MAX, T2M_MIN, T2M, RH2M, WS2M, ALLSKY_SFC_SW_DWN, PRECTOTCORR.
        latitude (float): Latitude for calculating extraterrestrial radiation (Ra), between -90 and 90.

    Returns:
        Tuple[pd.DataFrame, List[str]]: Validated DataFrame and list of warnings with metrics.

    Example:
        >>> df = pd.DataFrame({...}, index=pd.to_datetime([...]))
        >>> validated_df, warnings = data_initial_validate(df, latitude=-10.0)
    """
    logger.info("Validating weather data")
    warnings = []

    # Validate latitude
    if not (-90 <= latitude <= 90):
        warnings.append("Latitude must be between -90 and 90.")
        logger.error(warnings[-1])
        raise ValueError(warnings[-1])

    # Validate index
    if not pd.api.types.is_datetime64_any_dtype(weather_df.index):
        warnings.append("DataFrame index must be in datetime format (YYYY-MM-DD).")
        logger.error(warnings[-1])
        raise ValueError(warnings[-1])

    weather_df = weather_df.copy()
    weather_df["day_of_year"] = weather_df.index.dayofyear

    def is_leap_year(year: int) -> bool:
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    year = weather_df.index.year[0]
    total_days_in_year = 366 if is_leap_year(year) else 365

    # Calculate extraterrestrial radiation (Ra)
    phi = latitude * np.pi / 180
    day_of_year = weather_df["day_of_year"].to_numpy()
    dr = 1 + 0.033 * np.cos(2 * np.pi * day_of_year / total_days_in_year)
    delta = 0.409 * np.sin((2 * np.pi * day_of_year / total_days_in_year) - 1.39)
    omega_s = np.arccos(-np.tan(phi) * np.tan(delta))
    const = (24 * 60 * 0.0820) / np.pi
    Ra = const * dr * (omega_s * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(omega_s))
    weather_df["Ra"] = Ra
    if not (weather_df["Ra"] > 0).all():
        warnings.append("Invalid Ra values detected.")
        logger.error(warnings[-1])

    weather_df["dr"] = dr
    weather_df["delta"] = delta
    weather_df["omega_s"] = omega_s

    # Apply physical limits from Xavier et al. (2016, 2022)
    limits = {
        "T2M_MAX": (-30, 50, "left"),
        "T2M_MIN": (-30, 50, "left"),
        "T2M": (-30, 50, "left"),
        "RH2M": (0, 100, "left"),
        "WS2M": (0, 100, "left"),
        "PRECTOTCORR": (0, 450, "left"),
    }

    # Validate numeric columns
    for col, (min_val, max_val, inclusive) in limits.items():
        if col in weather_df.columns:
            initial_nans = weather_df[col].isna().sum()
            invalid_mask = ~weather_df[col].between(min_val, max_val, inclusive=inclusive)
            invalid_count = invalid_mask.sum()
            if invalid_count > 0:
                percent_invalid = (invalid_count / len(weather_df)) * 100
                warnings.append(
                    f"Invalid values in {col}: {invalid_count} records ({percent_invalid:.2f}%) replaced with NaN."
                )
                logger.warning(warnings[-1])
            weather_df[col] = weather_df[col].where(~invalid_mask, np.nan)

    # Validate solar radiation
    if "ALLSKY_SFC_SW_DWN" in weather_df.columns:
        initial_nans = weather_df["ALLSKY_SFC_SW_DWN"].isna().sum()
        invalid_rad_mask = ~weather_df["ALLSKY_SFC_SW_DWN"].between(
            0.03 * weather_df["Ra"], weather_df["Ra"], inclusive="left"
        )
        invalid_count = invalid_rad_mask.sum()
        if invalid_count > 0:
            percent_invalid = (invalid_count / len(weather_df)) * 100
            warnings.append(
                f"Invalid values in ALLSKY_SFC_SW_DWN: {invalid_count} records ({percent_invalid:.2f}%) replaced with NaN."
            )
            logger.warning(warnings[-1])
        weather_df["ALLSKY_SFC_SW_DWN"] = weather_df["ALLSKY_SFC_SW_DWN"].where(~invalid_rad_mask, np.nan)

    # Metric: Total invalid values
    invalid_rows = weather_df[weather_df.isna().any(axis=1)]
    if not invalid_rows.empty:
        total_invalid = invalid_rows.isna().sum().sum()
        percent_invalid = (total_invalid / (len(weather_df) * len(weather_df.columns))) * 100
        warnings.append(
            f"Total invalid values replaced with NaN: {total_invalid} ({percent_invalid:.2f}% of data)."
        )
        logger.info(warnings[-1])

    return weather_df, warnings


@shared_task
def detect_outliers_iqr(weather_df: pd.DataFrame, iqr_factor: float = 1.5) -> Tuple[pd.DataFrame, List[str]]:
    """
    Detect outliers using IQR method and replace them with NaN.

    Args:
        weather_df (pd.DataFrame): Weather data with numeric columns.
        iqr_factor (float): Factor for IQR bounds (default: 1.5 for moderate outliers).

    Returns:
        Tuple[pd.DataFrame, List[str]]: DataFrame with outliers replaced by NaN and list of warnings with metrics.
    """
    logger.info("Detecting outliers with IQR")
    warnings = []

    weather_df = weather_df.copy()
    numeric_cols = [
        col for col in weather_df.columns
        if col not in ["Ra", "dr", "delta", "omega_s"] and weather_df[col].dtype in [np.float64, np.int64]
    ]

    if not numeric_cols:
        warnings.append("No numeric columns available for outlier detection.")
        logger.warning(warnings[-1])
        return weather_df, warnings

    for col in numeric_cols:
        Q1 = weather_df[col].quantile(0.25)
        Q3 = weather_df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - iqr_factor * IQR
        upper_bound = Q3 + iqr_factor * IQR
        outlier_mask = (weather_df[col] < lower_bound) | (weather_df[col] > upper_bound)
        outlier_count = outlier_mask.sum()
        if outlier_count > 0:
            percent_outliers = (outlier_count / len(weather_df)) * 100
            warnings.append(
                f"Detected {outlier_count} outliers in {col} ({percent_outliers:.2f}%) using IQR."
            )
            logger.info(warnings[-1])
        weather_df[col] = weather_df[col].where(~outlier_mask, np.nan)

    return weather_df, warnings


@shared_task
def data_impute(weather_df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Impute missing weather data using linear interpolation (FAO-56 recommendation).

    Args:
        weather_df (pd.DataFrame): Weather data with missing values.

    Returns:
        Tuple[pd.DataFrame, List[str]]: Imputed DataFrame and list of warnings with metrics.
    """
    logger.info("Imputing missing weather data")
    warnings = []

    weather_df = weather_df.copy()
    numeric_cols = [
        col for col in weather_df.columns
        if col not in ["Ra", "dr", "delta", "omega_s"] and weather_df[col].dtype in [np.float64, np.int64]
    ]

    for col in numeric_cols:
        missing_count = weather_df[col].isna().sum()
        if missing_count > 0:
            percent_missing = (missing_count / len(weather_df)) * 100
            weather_df[col] = weather_df[col].interpolate(method="linear", limit_direction="both")
            warnings.append(
                f"Imputed {missing_count} missing values in {col} ({percent_missing:.2f}%) using linear interpolation."
            )
            logger.info(warnings[-1])

    # Check for remaining NaNs
    remaining_nans = weather_df[numeric_cols].isna().sum().sum()
    if remaining_nans > 0:
        percent_remaining = (remaining_nans / (len(weather_df) * len(numeric_cols))) * 100
        warnings.append(
            f"Warning: {remaining_nans} missing values ({percent_remaining:.2f}%) could not be imputed."
        )
        logger.warning(warnings[-1])
        # Fallback: Replace remaining NaNs with column mean
        for col in numeric_cols:
            if weather_df[col].isna().any():
                weather_df[col] = weather_df[col].fillna(weather_df[col].mean())
                warnings.append(f"Filled remaining NaNs in {col} with mean value.")
                logger.info(warnings[-1])

    return weather_df, warnings


@shared_task
def preprocessing(weather_df: pd.DataFrame, latitude: float, cache_key: Optional[str] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Preprocessing pipeline: validation, outlier detection, and imputation.

    Args:
        weather_df (pd.DataFrame): Weather data with datetime index.
        latitude (float): Latitude for Ra calculation, between -90 and 90.
        cache_key (Optional[str]): Key for caching results in Redis.

    Returns:
        Tuple[pd.DataFrame, List[str]]: Preprocessed DataFrame and list of warnings with metrics.

    Example:
        >>> df = pd.DataFrame({...}, index=pd.to_datetime([...]))
        >>> preprocessed_df, warnings = preprocessing(df, latitude=-10.0, cache_key="preprocess_20230101_-10.0_-45.0")
    """
    logger.info("Starting preprocessing pipeline")
    warnings = []

    # Validate input DataFrame
    if weather_df.empty:
        warnings.append("Input DataFrame is empty.")
        logger.error(warnings[-1])
        raise ValueError(warnings[-1])

    # Initialize Redis client
    redis_client = None
    if cache_key:
        try:
            redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            redis_client.ping()
            cached_data = redis_client.get(cache_key)
            if cached_data:
                df = pickle.loads(cached_data)
                logger.info(f"Loaded preprocessed data from Redis cache: {cache_key}")
                return df, ["Loaded from cache"]
        except redis.RedisError as e:
            warnings.append(f"Failed to access Redis cache: {e}")
            logger.error(warnings[-1])

    # Step 1: Initial validation
    weather_df, validate_warnings = data_initial_validate(weather_df, latitude)
    warnings.extend(validate_warnings)

    # Step 2: Outlier detection with IQR
    weather_df, outlier_warnings = detect_outliers_iqr(weather_df, iqr_factor=1.5)
    warnings.extend(outlier_warnings)

    # Step 3: Imputation
    weather_df, impute_warnings = data_impute(weather_df)
    warnings.extend(impute_warnings)

    # Save to cache
    if redis_client and cache_key:
        try:
            redis_client.setex(cache_key, timedelta(hours=CACHE_EXPIRY_HOURS), pickle.dumps(weather_df))
            logger.info(f"Saved preprocessed data to Redis cache: {cache_key}")
        except redis.RedisError as e:
            warnings.append(f"Failed to save to Redis cache: {e}")
            logger.error(warnings[-1])

    # Final metric: Total data altered
    total_altered = sum([int(w.split(" ")[1]) for w in warnings if "Invalid values" in w or "outliers" in w or "missing values" in w])
    percent_altered = (total_altered / (len(weather_df) * len(weather_df.columns))) * 100
    warnings.append(f"Total data altered during preprocessing: {total_altered} values ({percent_altered:.2f}%).")
    logger.info(warnings[-1])

    return weather_df, warnings