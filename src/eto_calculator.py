import numpy as np
import pandas as pd
from celery import Celery
from loguru import logger
from datetime import datetime
from src.data_preprocessing import preprocessing
from src.data_download import download_weather_data
from src.data_fusion import data_fusion

# Configuração do logging
logger.add("./logs/app.log", rotation="10 MB", retention="10 days", level="INFO")
logger.info("Iniciando cálculo de ET₀...")

# Configuração do Celery
app = Celery("processing", broker="redis://redis:6379/0", backend="redis://redis:6379/0")

def calculate_eto(weather_df: pd.DataFrame, elevation: float, latitude: float) -> tuple[pd.DataFrame, list]:
    """
    Calcula a evapotranspiração de referência (ETo) usando o método FAO-56 Penman-Monteith.

    Args:
        weather_df (pd.DataFrame): DataFrame com dados climáticos.
        elevation (float): Elevação em metros.
        latitude (float): Latitude em graus (-90 a 90).

    Returns:
        Tuple[pd.DataFrame, list]: DataFrame com ETo e lista de avisos.
    """
    warnings = []
    try:
        required_columns = [
            "T2M_MAX", "T2M_MIN", "T2M", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "day_of_year", "Ra"
        ]
        missing_columns = [col for col in required_columns if col not in weather_df.columns]
        if missing_columns:
            warnings.append(f"Colunas necessárias ausentes: {missing_columns}")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])

        if not pd.api.types.is_datetime64_any_dtype(weather_df.index):
            warnings.append("O índice do DataFrame deve estar no formato datetime (YYYY-MM-DD)")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])

        T2M_MAX = weather_df["T2M_MAX"].values
        T2M_MIN = weather_df["T2M_MIN"].values
        T2M = weather_df["T2M"].values
        RH2M = weather_df["RH2M"].values
        WS2M = weather_df["WS2M"].values
        ALLSKY_SFC_SW_DWN = weather_df["ALLSKY_SFC_SW_DWN"].values
        Ra = weather_df["Ra"].values

        if np.isnan(T2M).any():
            warnings.append("Valores NaN detectados em T2M")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])

        P = 101.3 * np.power(((293 - 0.0065 * elevation) / 293), 5.26)
        gamma = P * 0.665 * 1e-3
        es = (0.6108 * np.exp(17.27 * T2M_MIN / (T2M_MIN + 237.3)) + 
              0.6108 * np.exp(17.27 * T2M_MAX / (T2M_MAX + 237.3))) / 2
        ea = es * RH2M / 100
        Delta = 4098 * (0.6108 * np.exp(17.27 * T2M / (T2M + 237.3))) / (T2M + 237.3) ** 2

        weather_df["is_leap_year"] = weather_df.index.is_leap_year
        total_days_in_year = np.where(weather_df["is_leap_year"], 366, 365)

        Rso = (0.75 + (2 * elevation * 0.00001)) * Ra
        SIGMA = 4.903 * 1e-9
        Rnl = (SIGMA * (((T2M_MAX + 273.16) ** 4 + (T2M_MIN + 273.16) ** 4) / 2) * 
               (0.34 - 0.14 * np.sqrt(ea)) * 
               (1.35 * (ALLSKY_SFC_SW_DWN / np.where(Rso > 0, Rso, 1)) - 0.35))
        ALBEDO = 0.23
        Rns = (1 - ALBEDO) * ALLSKY_SFC_SW_DWN
        Rn = Rns - Rnl

        denominator = Delta + gamma * (1 + 0.34 * WS2M)
        ETo = np.where(
            denominator != 0,
            (0.408 * Delta * Rn + gamma * (900 / (T2M + 273)) * WS2M * (es - ea)) / denominator,
            np.nan,
        )

        weather_df["ETo"] = ETo
        logger.info("Cálculo de ETo concluído com sucesso")
        return weather_df[["T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "ETo"]], warnings
    except Exception as e:
        warnings.append(f"Erro no cálculo de ETo: {str(e)}")
        logger.error(warnings[-1])
        raise

@app.task
async def calculate_eto_pipeline(
    lat: float,
    lng: float,
    elevation: float,
    database: str,
    d_inicial: str,
    d_final: str,
    estado: str = None,
    cidade: str = None
) -> tuple[dict, list]:
    """
    Pipeline para download, pré-processamento, fusão de dados e cálculo de ETo.

    Args:
        lat (float): Latitude (-90 a 90).
        lng (float): Longitude (-180 a 180).
        elevation (float): Elevação em metros.
        database (str): Fonte de dados ('openmeteo_archive', 'openmeteo_forecast', 'nasa_power', 'Data Fusion').
        d_inicial (str): Data inicial (YYYY-MM-DD).
        d_final (str): Data final (YYYY-MM-DD).
        estado (str, optional): Estado para modo MATOPIBA.
        cidade (str, optional): Cidade para modo MATOPIBA.

    Returns:
        Tuple[dict, list]: Dados de ETo em formato dicionário e lista de avisos.
    """
    warnings = []
    try:
        logger.info("Iniciando pipeline de cálculo de ETo")

        # Validação de parâmetros
        if not (-90 <= lat <= 90):
            warnings.append("Latitude must be between -90 and 90.")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])
        if not (-180 <= lng <= 180):
            warnings.append("Longitude must be between -180 and 180.")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])
        if elevation < -1000 or elevation > 9000:
            warnings.append("Elevation must be between -1000 and 9000 meters.")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])
        valid_databases = ["openmeteo_archive", "openmeteo_forecast", "nasa_power", "Data Fusion"]
        if database not in valid_databases:
            warnings.append(f"Invalid database. Use one of: {valid_databases}")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])
        try:
            start = datetime.strptime(d_inicial, "%Y-%m-%d")
            end = datetime.strptime(d_final, "%Y-%m-%d")
        except ValueError:
            warnings.append("Invalid date format. Use YYYY-MM-DD.")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])
        if end < start:
            warnings.append("End date must be after start date.")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])
        period_days = (end - start).days + 1
        if period_days < 7 or period_days > 15:
            warnings.append("Period must be between 7 and 15 days.")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])
        if (estado or cidade) and not (estado and cidade):
            warnings.append("Both estado and cidade must be provided for MATOPIBA mode.")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])

        # Download de dados climáticos
        logger.info("Baixando dados climáticos")
        weather_data, download_warnings = await download_weather_data(database, d_inicial, d_final, lng, lat)
        warnings.extend(download_warnings)
        if weather_data is None or not isinstance(weather_data, pd.DataFrame) or weather_data.empty:
            warnings.append("Falha ao baixar dados climáticos")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])

        # Pré-processamento
        logger.info("Pré-processando dados")
        task = preprocessing.delay(weather_data.to_dict(), lat)
        forecast_data_dict, preprocess_warnings = task.get(timeout=10)
        warnings.extend(preprocess_warnings)
        forecast_data = pd.DataFrame(forecast_data_dict)
        if forecast_data is None or forecast_data.empty:
            warnings.append("Falha no pré-processamento dos dados")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])

        # Fusão de dados (se selecionado)
        if database == "Data Fusion":
            logger.info("Aplicando fusão de dados")
            try:
                task = data_fusion.delay([forecast_data.to_dict(), weather_data.to_dict()])
                fused_data_dict, fusion_warnings = task.get(timeout=10)
                warnings.extend(fusion_warnings)
                weather_data = pd.DataFrame(fused_data_dict)
                if weather_data.empty:
                    warnings.append("Fusão de dados retornou DataFrame vazio")
                    logger.error(warnings[-1])
                    raise ValueError(warnings[-1])
            except Exception as e:
                warnings.append(f"Erro na fusão de dados: {str(e)}")
                logger.error(warnings[-1])
                raise ValueError(warnings[-1])

        # Cálculo de ETo
        logger.info("Calculando ETo")
        eto_df, eto_warnings = calculate_eto(forecast_data, elevation, lat)
        warnings.extend(eto_warnings)
        if eto_df is None or eto_df.empty:
            warnings.append("Falha no cálculo de ETo")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])

        logger.info("Pipeline concluído com sucesso")
        return eto_df.to_dict(), warnings
    except Exception as e:
        warnings.append(f"Erro no pipeline: {str(e)}")
        logger.error(warnings[-1])
        return {}, warnings