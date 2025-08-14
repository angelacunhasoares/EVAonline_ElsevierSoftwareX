import numpy as np
import pandas as pd
from celery import Celery
from loguru import logger
import requests_cache
from src.data_preprocessing import preprocessing
from src.data_download import download_weather_data
from src.data_fusion import data_fusion
logger.add("./logs/app.log", rotation="10 MB", retention="10 days", level="INFO")
logger.info("Iniciando cálculo de ET₀...")
requests_cache.install_cache('./data/.cache', backend='sqlite')

app = Celery("processing", broker="redis://redis:6379/0", backend="redis://redis:6379/0")


def calculate_eto(weather_df: pd.DataFrame, elevation: float, latitude: float) -> pd.DataFrame:
    """
    Calcula a evapotranspiração de referência (ETo) usando o método FAO-56 Penman-Monteith.
    """
    try:
        required_columns = [
            "T2M_MAX", "T2M_MIN", "T2M", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "day_of_year", "Ra"
        ]
        missing_columns = [col for col in required_columns if col not in weather_df.columns]
        if missing_columns:
            logger.error(f"Colunas necessárias ausentes: {missing_columns}")
            raise ValueError(f"Colunas necessárias ausentes: {missing_columns}")

        if not pd.api.types.is_datetime64_any_dtype(weather_df["date"]):
            logger.error("A coluna 'date' deve estar no formato datetime (YYYY-MM-DD)")
            raise ValueError("A coluna 'date' deve estar no formato datetime (YYYY-MM-DD)")

        T2M_MAX = weather_df["T2M_MAX"].values
        T2M_MIN = weather_df["T2M_MIN"].values
        T2M = weather_df["T2M"].values
        RH2M = weather_df["RH2M"].values
        WS2M = weather_df["WS2M"].values
        ALLSKY_SFC_SW_DWN = weather_df["ALLSKY_SFC_SW_DWN"].values
        Ra = weather_df["Ra"].values

        if np.isnan(T2M).any():
            logger.error("Valores NaN detectados em T2M")
            raise ValueError("Valores NaN detectados em T2M")

        P = 101.3 * np.power(((293 - 0.0065 * elevation) / 293), 5.26)
        gamma = P * 0.665 * 1e-3
        es = (0.6108 * np.exp(17.27 * T2M_MIN / (T2M_MIN + 237.3)) + 
              0.6108 * np.exp(17.27 * T2M_MAX / (T2M_MAX + 237.3))) / 2
        ea = es * RH2M / 100
        Delta = 4098 * (0.6108 * np.exp(17.27 * T2M / (T2M + 237.3))) / (T2M + 237.3) ** 2

        weather_df["is_leap_year"] = weather_df["date"].dt.is_leap_year
        total_days_in_year = np.where(weather_df["is_leap_year"], 366, 365)

        Rso = (0.75 + (2 * elevation * 0.00001)) * Ra
        SIGMA = 4.903 * 10**-9
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
        return weather_df[["date", "T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "ETo"]]
    except Exception as e:
        logger.error(f"Erro no cálculo de ETo: {str(e)}")
        raise


@app.task
async def calculate_eto_pipeline(lat: float, lng: float, elevation: float, database: str, d_inicial: str, d_final: str, estado: str = None, cidade: str = None) -> tuple[dict, list]:
    """
    Pipeline para download, pré-processamento, fusão de dados e cálculo de ETo.
    """
    try:
        logger.info("Iniciando pipeline de cálculo de ETo")
        required_params = {"lat", "lng", "elevation", "database", "d_inicial", "d_final"}
        params = {"lat": lat, "lng": lng, "elevation": elevation, "database": database, "d_inicial": d_inicial, "d_final": d_final}
        for key, value in params.items():
            if value is None and key in required_params:
                logger.error(f"Parâmetro '{key}' não pode ser None")
                raise ValueError(f"Parâmetro '{key}' não pode ser None")

        # Download de dados climáticos
        logger.info("Baixando dados climáticos")
        weather_data, warnings = await download_weather_data(database, d_inicial, d_final, lng, lat)
        if weather_data is None or not isinstance(weather_data, pd.DataFrame):
            logger.error("Falha ao baixar dados climáticos")
            raise ValueError("Falha ao baixar dados climáticos")

        # Pré-processamento
        logger.info("Pré-processando dados")
        forecast_data = preprocessing(weather_data, lat)
        
        # Fusão de dados (se selecionado)
        if database == "Data Fusion":
            logger.info("Aplicando fusão de dados")
            weather_data = data_fusion.delay(forecast_data.to_dict(), weather_data.to_dict()).get()
            weather_data = pd.DataFrame(weather_data)

        # Cálculo de ETo
        logger.info("Calculando ETo")
        eto_df = calculate_eto(weather_data, elevation, lat)
        
        logger.info("Pipeline concluído com sucesso")
        return eto_df.to_dict(), warnings
    except Exception as e:
        logger.error(f"Erro no pipeline: {str(e)}")
        raise