import logging
from datetime import datetime
from typing import Union, Tuple
import numpy as np
import pandas as pd
from celery import shared_task
from api.nasapower import NasaPowerAPI
from api.openmeteo import OpenMeteoArchiveAPI, OpenMeteoForecastAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shared_task
async def download_weather_data(
    data_source: Union[str, list],
    data_inicial: str,
    data_final: str,
    longitude: float,
    latitude: float,
) -> Tuple[pd.DataFrame, list]:
    """
    Download weather data from specified sources for given coordinates and date range.
    
    Args:
        data_source: Data source ("NASA POWER", "Open-Meteo Archive", "Open-Meteo Forecast", or "Data Fusion")
        data_inicial: Start date in dd/mm/yyyy format
        data_final: End date in dd/mm/yyyy format
        longitude: Longitude (-180 to 180)
        latitude: Latitude (-90 to 90)
    
    Returns:
        Tuple[pd.DataFrame, list]: Weather data DataFrame and list of warnings
    
    Example:
        >>> df, warnings = await download_weather_data(
        ...     data_source="Data Fusion",
        ...     data_inicial="01/01/2023",
        ...     data_final="07/01/2023",
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
        raise ValueError("Latitude must be between -90 and 90.")
    if not (-180 <= longitude <= 180):
        raise ValueError("Longitude must be between -180 and 180.")

    # Validate dates
    try:
        data_inicial_formatted = pd.to_datetime(data_inicial, format="%d/%m/%Y")
        data_final_formatted = pd.to_datetime(data_final, format="%d/%m/%Y")
    except ValueError:
        raise ValueError("Dates must be in 'dd/mm/yyyy' format.")

    if data_final_formatted < data_inicial_formatted:
        raise ValueError("End date must be after start date.")

    period_days = (data_final_formatted - data_inicial_formatted).days + 1
    if not (7 <= period_days <= 15):
        raise ValueError("Period must be between 7 and 15 days.")

    # Define sources
    if data_source == "Data Fusion":
        sources = ["NASA POWER", "Open-Meteo Archive", "Open-Meteo Forecast"]
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
            if source == "NASA POWER"
            else data_final_formatted
        )
        if data_final_adjusted < data_final_formatted:
            warnings_list.append(
                f"NASA POWER data truncated to {data_final_adjusted.strftime('%d/%m/%Y')} "
                "as it does not provide future data."
            )

        # Download data
        try:
            if source == "NASA POWER":
                nasa_weather = NasaPowerAPI(
                    start=data_inicial_formatted,
                    end=data_final_adjusted,
                    long=longitude,
                    lat=latitude,
                    use_cache=True,
                    matopiba_only=(mode == "MATOPIBA")  # Passar modo MATOPIBA
                )
                weather_df = await nasa_weather.get_weather()
                logger.info(f"Downloaded data from NASA POWER for lat={latitude}, lng={longitude}")

            elif source == "Open-Meteo Archive":
                open_meteo = OpenMeteoArchiveAPI(
                    start=data_inicial_formatted,
                    end=data_final_adjusted,
                    long=longitude,
                    lat=latitude,
                    use_cache=True,
                )
                weather_df, fetch_warnings = await open_meteo.get_weather()
                warnings_list.extend(fetch_warnings)
                logger.info(f"Downloaded data from Open-Meteo Archive for lat={latitude}, lng={longitude}")

            elif source == "Open-Meteo Forecast":
                open_meteo = OpenMeteoForecastAPI(
                    start=data_inicial_formatted,
                    end=data_final_adjusted,
                    long=longitude,
                    lat=latitude,
                    use_cache=True,
                )
                weather_df, fetch_warnings = await open_meteo.get_weather()
                warnings_list.extend(fetch_warnings)
                logger.info(f"Downloaded data from Open-Meteo Forecast for lat={latitude}, lng={longitude}")

            # Validate and process DataFrame
            if weather_df is None or weather_df.empty:
                logger.warning(
                    f"No data retrieved from {source} for {latitude}, {longitude} between {data_inicial} and {data_final}."
                )
                warnings_list.append(f"No data retrieved from {source}.")
                continue

            # Ensure date column
            if "date" not in weather_df.columns:
                weather_df = weather_df.reset_index().rename(columns={"index": "date"})

            # Standardize columns
            expected_columns = [
                "date", "T2M_MAX", "T2M_MIN", "T2M", "RH2M", "WS2M",
                "ALLSKY_SFC_SW_DWN", "PRECTOTCORR"
            ]
            for col in expected_columns:
                if col not in weather_df.columns:
                    weather_df[col] = np.nan

            # Filter expected columns
            weather_df = weather_df[expected_columns]
            weather_df = weather_df.replace(-999.00, np.nan)
            weather_df = weather_df.dropna(how="all", subset=weather_df.columns.difference(["date"]))

            # Check for missing data
            returned_days = (weather_df["date"].max() - weather_df["date"].min()).days + 1
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
            raise ValueError("At least two valid data sources are required for fusion.")
        try:
            from src.eto_calculator import data_fusion
            weather_data = data_fusion(dfs)
            logger.info("Data fusion completed successfully.")
        except Exception as e:
            logger.error(f"Error during data fusion: {str(e)}")
            raise ValueError(f"Data fusion failed: {str(e)}")
    else:
        if not dfs:
            raise ValueError("No valid data sources provided data.")
        weather_data = dfs[0]

    # Final validation
    expected_columns = [
        "date", "T2M_MAX", "T2M_MIN", "T2M", "RH2M", "WS2M",
        "ALLSKY_SFC_SW_DWN", "PRECTOTCORR"
    ]
    missing_columns = [col for col in expected_columns if col not in weather_data.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    logger.info(f"Final weather data:\n{weather_data.to_string()}")
    return weather_data, warnings_list