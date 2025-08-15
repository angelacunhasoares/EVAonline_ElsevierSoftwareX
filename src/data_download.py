from datetime import datetime
from typing import Union, Tuple, List
import numpy as np
import pandas as pd
from celery import shared_task
from loguru import logger
from api.nasapower import NasaPowerAPI
from api.openmeteo import OpenMeteoArchiveAPI, OpenMeteoForecastAPI
from src.data_fusion import data_fusion

@shared_task
async def download_weather_data(
    data_source: Union[str, list],
    data_inicial: str,
    data_final: str,
    longitude: float,
    latitude: float,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Download weather data from specified sources for given coordinates and date range.
    
    Args:
        data_source: Data source ("nasa_power", "openmeteo_archive", "openmeteo_forecast", or "Data Fusion")
        data_inicial: Start date in YYYY-MM-DD format
        data_final: End date in YYYY-MM-DD format
        longitude: Longitude (-180 to 180)
        latitude: Latitude (-90 to 90)
    
    Returns:
        Tuple[pd.DataFrame, List[str]]: Weather data DataFrame and list of warnings
    
    Example:
        >>> df, warnings = await download_weather_data(
        ...     data_source="Data Fusion",
        ...     data_inicial="2023-01-01",
        ...     data_final="2023-01-07",
        ...     longitude=-45.0,
        ...     latitude=-10.0
        ... )
    """
    logger.info("Entrou na função download_weather_data")
    logger.debug(f"Data source: {data_source}, Data inicial: {data_inicial}, Data final: {data_final}, "
                 f"Latitude: {latitude}, Longitude: {longitude}")

    warnings_list = []

    # Validate coordinates
    if not (-90 <= latitude <= 90):
        warnings_list.append("Latitude must be between -90 and 90.")
        logger.error(warnings_list[-1])
        raise ValueError(warnings_list[-1])
    if not (-180 <= longitude <= 180):
        warnings_list.append("Longitude must be between -180 and 180.")
        logger.error(warnings_list[-1])
        raise ValueError(warnings_list[-1])

    # Validate dates
    try:
        data_inicial_formatted = pd.to_datetime(data_inicial, format="%Y-%m-%d")
        data_final_formatted = pd.to_datetime(data_final, format="%Y-%m-%d")
    except ValueError:
        warnings_list.append("Dates must be in 'YYYY-MM-DD' format.")
        logger.error(warnings_list[-1])
        raise ValueError(warnings_list[-1])

    if data_final_formatted < data_inicial_formatted:
        warnings_list.append("End date must be after start date.")
        logger.error(warnings_list[-1])
        raise ValueError(warnings_list[-1])

    period_days = (data_final_formatted - data_inicial_formatted).days + 1
    if not (7 <= period_days <= 15):
        warnings_list.append("Period must be between 7 and 15 days.")
        logger.error(warnings_list[-1])
        raise ValueError(warnings_list[-1])

    # Validate data source
    valid_sources = ["nasa_power", "openmeteo_archive", "openmeteo_forecast", "Data Fusion"]
    if data_source not in valid_sources:
        warnings_list.append(f"Invalid data source: {data_source}. Use one of: {valid_sources}")
        logger.error(warnings_list[-1])
        raise ValueError(warnings_list[-1])

    # Define sources
    if data_source == "Data Fusion":
        sources = ["nasa_power", "openmeteo_archive", "openmeteo_forecast"]
        logger.info("Data Fusion selecionada, coletando dados de múltiplas fontes.")
    else:
        sources = [data_source]
        logger.info(f"Fonte única selecionada: {data_source}")

    current_date = pd.to_datetime(datetime.now().date())
    dfs = []
    for source in sources:
        # Adjust end date for NASA POWER (no future data)
        data_final_adjusted = (
            min(data_final_formatted, current_date)
            if source == "nasa_power"
            else data_final_formatted
        )
        if data_final_adjusted < data_final_formatted:
            warnings_list.append(
                f"NASA POWER data truncated to {data_final_adjusted.strftime('%Y-%m-%d')} "
                "as it does not provide future data."
            )

        # Download data
        try:
            if source == "nasa_power":
                api = NasaPowerAPI(
                    start=data_inicial_formatted,
                    end=data_final_adjusted,
                    long=longitude,
                    lat=latitude
                )
                weather_df, fetch_warnings = await api.get_weather()
                warnings_list.extend(fetch_warnings)
                logger.info(f"Downloaded data from NASA POWER for lat={latitude}, lng={longitude}")

            elif source == "openmeteo_archive":
                api = OpenMeteoArchiveAPI(
                    start=data_inicial_formatted,
                    end=data_final_adjusted,
                    long=longitude,
                    lat=latitude
                )
                weather_df, fetch_warnings = await api.get_weather()
                warnings_list.extend(fetch_warnings)
                logger.info(f"Downloaded data from Open-Meteo Archive for lat={latitude}, lng={longitude}")

            elif source == "openmeteo_forecast":
                api = OpenMeteoForecastAPI(
                    start=data_inicial_formatted,
                    end=data_final_adjusted,
                    long=longitude,
                    lat=latitude
                )
                weather_df, fetch_warnings = await api.get_weather()
                warnings_list.extend(fetch_warnings)
                logger.info(f"Downloaded data from Open-Meteo Forecast for lat={latitude}, lng={longitude}")

            # Validate DataFrame
            if weather_df is None or weather_df.empty:
                logger.warning(
                    f"No data retrieved from {source} for lat={latitude}, lng={longitude} "
                    f"between {data_inicial} and {data_final}."
                )
                warnings_list.append(f"No data retrieved from {source}.")
                continue

            # Standardize columns
            expected_columns = [
                "T2M_MAX", "T2M_MIN", "T2M", "RH2M", "WS2M",
                "ALLSKY_SFC_SW_DWN", "PRECTOTCORR"
            ]
            for col in expected_columns:
                if col not in weather_df.columns:
                    weather_df[col] = np.nan

            # Filter expected columns
            weather_df = weather_df[expected_columns]
            weather_df = weather_df.replace(-999.00, np.nan)
            weather_df = weather_df.dropna(how="all", subset=weather_df.columns)

            # Check for missing data
            returned_days = (weather_df.index.max() - weather_df.index.min()).days + 1
            if returned_days < period_days:
                warnings_list.append(
                    f"{source} returned only {returned_days} days of data (requested {period_days} days)."
                )

            # Check missing data percentage
            missing_percent = weather_df.isna().mean() * 100
            variable_mapping = {
                "ALLSKY_SFC_SW_DWN": "Radiação Solar (MJ/m²/dia)",
                "PRECTOTCORR": "Precipitação Total (mm)",
                "T2M_MAX": "Temperatura Máxima (°C)",
                "T2M_MIN": "Temperatura Mínima (°C)",
                "T2M": "Temperatura Média (°C)",
                "RH2M": "Umidade Relativa (%)",
                "WS2M": "Velocidade do Vento (m/s)",
            }
            for col, percent in missing_percent.items():
                if percent > 25:
                    friendly_col = variable_mapping.get(col, col)
                    warnings_list.append(
                        f"{source} has {percent:.2f}% missing data for {friendly_col}. "
                        "Imputation will be applied, which may affect ETo accuracy."
                    )

            dfs.append(weather_df)
            logger.info(f"{source} DataFrame:\n{weather_df.to_string()}")

        except Exception as e:
            logger.error(f"Error downloading from {source}: {str(e)}")
            warnings_list.append(f"Error downloading from {source}: {str(e)}")
            continue

    # Perform fusion if required
    if data_source == "Data Fusion":
        if len(dfs) < 2:
            warnings_list.append("At least two valid data sources are required for fusion.")
            logger.error(warnings_list[-1])
            raise ValueError(warnings_list[-1])
        try:
            task = data_fusion.delay([df.to_dict() for df in dfs])
            weather_data_dict, fusion_warnings = task.get(timeout=10)
            warnings_list.extend(fusion_warnings)
            weather_data = pd.DataFrame(weather_data_dict)
            logger.info("Data fusion completed successfully.")
        except Exception as e:
            warnings_list.append(f"Data fusion failed: {str(e)}")
            logger.error(warnings_list[-1])
            raise ValueError(warnings_list[-1])
    else:
        if not dfs:
            warnings_list.append("No valid data sources provided data.")
            logger.error(warnings_list[-1])
            raise ValueError(warnings_list[-1])
        weather_data = dfs[0]

    # Final validation
    expected_columns = [
        "T2M_MAX", "T2M_MIN", "T2M", "RH2M", "WS2M",
        "ALLSKY_SFC_SW_DWN", "PRECTOTCORR"
    ]
    missing_columns = [col for col in expected_columns if col not in weather_data.columns]
    if missing_columns:
        warnings_list.append(f"Missing required columns: {missing_columns}")
        logger.error(warnings_list[-1])
        raise ValueError(warnings_list[-1])

    logger.info(f"Final weather data:\n{weather_data.to_string()}")
    return weather_data, warnings_list