"""
Módulo para cálculo da Evapotranspiração de Referência (ETo) usando o método FAO-56 Penman-Monteith.

Este módulo implementa:
- Cálculo de ETo seguindo a metodologia FAO
- Pipeline completo de processamento de dados
- Integração com diferentes fontes de dados
- Suporte ao modo MATOPIBA
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from loguru import logger

from backend.core.data_processing.data_download import download_weather_data
from backend.core.data_processing.data_fusion import data_fusion
from backend.core.data_processing.data_preprocessing import preprocessing

# Configuração do logging
logger.add(
    "./logs/eto_calculator.log",
    rotation="10 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# Importar instância do Celery já configurada
from backend.infrastructure.celery.celery_config import celery_app as app

# Constantes
MATOPIBA_BOUNDS = {
    'lat_min': -14.5,
    'lat_max': -2.5,
    'lng_min': -50.0,
    'lng_max': -41.5
}


def calculate_eto(
    weather_df: pd.DataFrame, 
    elevation: float, 
    latitude: float
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Calcula a evapotranspiração de referência (ETo) usando o método FAO-56 Penman-Monteith.

    Args:
        weather_df: DataFrame com dados climáticos.
        elevation: Elevação em metros.
        latitude: Latitude em graus (-90 a 90).

    Returns:
        Tuple contendo:
        - DataFrame com ETo calculada
        - Lista de avisos/erros
    """
    warnings = []
    try:
        required_columns = [
            "T2M_MAX", "T2M_MIN", "T2M", "RH2M", "WS2M", 
            "ALLSKY_SFC_SW_DWN", "day_of_year", "Ra"
        ]
        missing_columns = [
            col for col in required_columns 
            if col not in weather_df.columns
        ]
        if missing_columns:
            msg = f"Colunas necessárias ausentes: {missing_columns}"
            warnings.append(msg)
            logger.error(msg)
            raise ValueError(msg)

        if not pd.api.types.is_datetime64_any_dtype(weather_df.index):
            msg = "O índice do DataFrame deve estar no formato datetime"
            warnings.append(msg)
            logger.error(msg)
            raise ValueError(msg)

        # Extrair arrays numpy para melhor performance
        T2M_MAX = np.array(weather_df["T2M_MAX"])
        T2M_MIN = np.array(weather_df["T2M_MIN"])
        T2M = np.array(weather_df["T2M"])
        RH2M = np.array(weather_df["RH2M"])
        WS2M = np.array(weather_df["WS2M"])
        ALLSKY_SFC_SW_DWN = np.array(weather_df["ALLSKY_SFC_SW_DWN"])
        Ra = np.array(weather_df["Ra"])

        # Validar dados
        if np.any(np.isnan([T2M, RH2M, WS2M, ALLSKY_SFC_SW_DWN, Ra])):
            msg = "Valores NaN detectados nos dados meteorológicos"
            warnings.append(msg)
            logger.error(msg)
            raise ValueError(msg)

        # Cálculos FAO-56
        P = 101.3 * ((293 - 0.0065 * elevation) / 293) ** 5.26
        gamma = P * 0.665e-3

        es = 0.6108 * (
            np.exp(17.27 * T2M_MIN / (T2M_MIN + 237.3)) + 
            np.exp(17.27 * T2M_MAX / (T2M_MAX + 237.3))
        ) / 2

        ea = es * RH2M / 100
        Delta = (
            4098 * 0.6108 * np.exp(17.27 * T2M / (T2M + 237.3)) / 
            (T2M + 237.3) ** 2
        )

        # Ensure index is datetime and get years
        years = pd.to_datetime(weather_df.index).year
        is_leap_year = [pd.Timestamp(str(year)).is_leap_year for year in years]
        total_days_in_year = np.where(is_leap_year, 366, 365)

        Rso = (0.75 + 2e-5 * elevation) * Ra
        SIGMA = 4.903e-9
        
        Rnl = (
            SIGMA * ((T2M_MAX + 273.16) ** 4 + (T2M_MIN + 273.16) ** 4) / 2 *
            (0.34 - 0.14 * np.sqrt(ea)) * 
            (1.35 * np.divide(
                ALLSKY_SFC_SW_DWN, 
                np.where(Rso > 0, Rso, 1)
            ) - 0.35)
        )

        ALBEDO = 0.23
        Rns = (1 - ALBEDO) * ALLSKY_SFC_SW_DWN
        Rn = Rns - Rnl

        denominator = Delta + gamma * (1 + 0.34 * WS2M)
        ETo = np.where(
            denominator != 0,
            (0.408 * Delta * Rn + gamma * (900 / (T2M + 273)) * WS2M * (es - ea)) / 
            denominator,
            np.nan
        )

        # Atualizar DataFrame
        weather_df["ETo"] = ETo
        result_columns = [
            "T2M_MAX", "T2M_MIN", "RH2M", "WS2M", 
            "ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "ETo"
        ]
        
        logger.info("Cálculo de ETo concluído com sucesso")
        return weather_df[result_columns], warnings

    except Exception as e:
        msg = f"Erro no cálculo de ETo: {str(e)}"
        warnings.append(msg)
        logger.error(msg)
        raise


@app.task(
    bind=True, 
    name='backend.core.eto_calculation.eto_calculation.calculate_eto_pipeline'
)
async def calculate_eto_pipeline(
    self,
    lat: float,
    lng: float,
    elevation: float,
    database: str,
    d_inicial: str,
    d_final: str,
    estado: Optional[str] = None,
    cidade: Optional[str] = None
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Pipeline completo para cálculo de ETo.

    Este pipeline realiza:
    1. Validação de parâmetros de entrada
    2. Download de dados meteorológicos
    3. Pré-processamento dos dados
    4. Cálculo da ETo
    5. Fusão de dados (quando aplicável)

    Args:
        lat: Latitude (-90 a 90)
        lng: Longitude (-180 a 180)
        elevation: Elevação em metros
        database: Base de dados ('nasa_power' ou 'openmeteo_forecast')
        d_inicial: Data inicial (YYYY-MM-DD)
        d_final: Data final (YYYY-MM-DD)
        estado: Estado para modo MATOPIBA
        cidade: Cidade para modo MATOPIBA

    Returns:
        Tuple contendo:
        - Dicionário com dados de ETo
        - Lista de avisos/erros
    """
    warnings = []
    try:
        # Validar coordenadas
        if not (-90 <= lat <= 90):
            raise ValueError("Latitude deve estar entre -90 e 90 graus")
        if not (-180 <= lng <= 180):
            raise ValueError("Longitude deve estar entre -180 e 180 graus")

        # Validar database
        valid_databases = ["nasa_power", "openmeteo_forecast"]
        if database not in valid_databases:
            raise ValueError(f"Base de dados inválida. Use: {valid_databases}")

        # Validar datas
        try:
            start = datetime.strptime(d_inicial, "%Y-%m-%d")
            end = datetime.strptime(d_final, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Formato de data inválido. Use: YYYY-MM-DD")

        # Validar período
        hoje = datetime.now()
        um_ano_atras = hoje - timedelta(days=365)
        amanha = hoje + timedelta(days=1)

        if start < um_ano_atras:
            raise ValueError("Data inicial não pode ser anterior a 1 ano atrás")
        if end > amanha:
            raise ValueError("Data final não pode ser posterior a amanhã")
        if end < start:
            raise ValueError("Data final deve ser posterior à data inicial")

        period_days = (end - start).days + 1
        if period_days < 7 or period_days > 15:
            raise ValueError("O período deve ser entre 7 e 15 dias")

        # Validar modo MATOPIBA
        is_matopiba = database == "openmeteo_forecast"
        if is_matopiba:
            if not (estado and cidade):
                raise ValueError(
                    "Estado e cidade são obrigatórios para o modo MATOPIBA"
                )
            if not (
                MATOPIBA_BOUNDS['lat_min'] <= lat <= MATOPIBA_BOUNDS['lat_max'] and
                MATOPIBA_BOUNDS['lng_min'] <= lng <= MATOPIBA_BOUNDS['lng_max']
            ):
                warnings.append(
                    "Coordenadas fora da região típica do MATOPIBA"
                )

        # Download dos dados primários
        weather_data, download_warnings = download_weather_data(
            database, d_inicial, d_final, lng, lat
        )
        warnings.extend(download_warnings)

        if weather_data is None or weather_data.empty:
            raise ValueError("Falha ao obter dados meteorológicos")

        # Se estiver no modo global, tenta buscar dados adicionais para fusão
        additional_data = []
        if database == "nasa_power":
            try:
                # Tentar obter dados de outras fontes disponíveis
                for additional_source in ["met_norway", "nws", "noaa_cdo"]:
                    try:
                        extra_data, extra_warnings = download_weather_data(
                            additional_source, d_inicial, d_final, lng, lat
                        )
                        if extra_data is not None and not extra_data.empty:
                            additional_data.append(extra_data)
                            warnings.extend(extra_warnings)
                    except Exception as e:
                        warnings.append(
                            f"Erro ao obter dados de {additional_source}: {str(e)}"
                        )
                
                # Se tiver dados adicionais, realizar fusão
                if additional_data:
                    all_data = [weather_data] + additional_data
                    fused_data, fusion_warnings = await data_fusion(
                        [df.to_dict() for df in all_data]
                    )
                    warnings.extend(fusion_warnings)
                    
                    if fused_data:
                        weather_data = pd.DataFrame.from_dict(fused_data)
                        logger.info("Fusão de dados realizada com sucesso")
                    else:
                        warnings.append("Fusão de dados falhou, usando dados primários")
                
            except Exception as e:
                warnings.append(f"Erro no processo de fusão: {str(e)}")
                logger.error(f"Erro na fusão de dados: {str(e)}")
                # Continua com os dados primários em caso de erro

        # Pré-processamento
        weather_data, preprocessing_warnings = preprocessing(weather_data, lat)
        warnings.extend(preprocessing_warnings)
        
        # Cálculo de ETo
        result_df, calc_warnings = calculate_eto(weather_data, elevation, lat)
        warnings.extend(calc_warnings)

        # Retornar resultados
        return {'data': result_df.to_dict(orient='records')}, warnings

    except Exception as e:
        msg = f"Erro no pipeline de ETo: {str(e)}"
        warnings.append(msg)
        logger.error(msg)
        return {}, warnings
