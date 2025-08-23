from datetime import datetime
from typing import Union, Tuple, List
import numpy as np
import pandas as pd
from celery import shared_task
from loguru import logger
from api.nasapower import NasaPowerAPI
from api.openmeteo import OpenMeteoForecastAPI
from src.data_fusion import data_fusion

@shared_task
def download_weather_data(
    data_source: Union[str, list],
    data_inicial: str,
    data_final: str,
    longitude: float,
    latitude: float,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Baixa dados meteorológicos das fontes especificadas para as coordenadas e período.
    
    Args:
        data_source: Fonte de dados ("nasa_power", "openmeteo_archive", 
                    "openmeteo_forecast", ou "Data Fusion")
        data_inicial: Data inicial no formato YYYY-MM-DD
        data_final: Data final no formato YYYY-MM-DD
        longitude: Longitude (-180 a 180)
        latitude: Latitude (-90 a 90)
    
    Returns:
        Tuple[pd.DataFrame, List[str]]: DataFrame com dados e lista de avisos
    
    Example:
        >>> df, warnings = download_weather_data(
        ...     data_source="Data Fusion",
        ...     data_inicial="2023-01-01",
        ...     data_final="2023-01-07",
        ...     longitude=-45.0,
        ...     latitude=-10.0
        ... )
    """
    logger.info(
        f"Iniciando download - Fonte: {data_source}, "
        f"Período: {data_inicial} a {data_final}, "
        f"Coord: ({latitude}, {longitude})"
    )
    warnings_list = []

    # Validação das coordenadas
    if not (-90 <= latitude <= 90):
        msg = "Latitude deve estar entre -90 e 90 graus"
        logger.error(msg)
        raise ValueError(msg)
    if not (-180 <= longitude <= 180):
        msg = "Longitude deve estar entre -180 e 180 graus"
        logger.error(msg)
        raise ValueError(msg)

    # Validação das datas
    try:
        data_inicial_formatted = pd.to_datetime(data_inicial)
        data_final_formatted = pd.to_datetime(data_final)
    except ValueError:
        msg = "As datas devem estar no formato 'AAAA-MM-DD'"
        logger.error(msg)
        raise ValueError(msg)

    # Verifica se é uma data válida (não futura para dados históricos)
    data_atual = pd.to_datetime(datetime.now().date())
    if data_inicial_formatted > data_atual:
        msg = (
            "A data inicial não pode ser futura para dados históricos. "
            f"Data atual: {data_atual.strftime('%Y-%m-%d')}"
        )
        logger.error(msg)
        raise ValueError(msg)

    # Verifica ordem das datas
    if data_final_formatted < data_inicial_formatted:
        msg = "A data final deve ser posterior à data inicial"
        logger.error(msg)
        raise ValueError(msg)

    # Verifica período mínimo e máximo
    period_days = (data_final_formatted - data_inicial_formatted).days + 1
    if period_days < 1:
        msg = "O período deve ter pelo menos 1 dia"
        logger.error(msg)
        raise ValueError(msg)
    
    # Limita período máximo para evitar sobrecarga
    max_period = 366  # 1 ano
    if period_days > max_period:
        msg = f"O período máximo permitido é de {max_period} dias"
        logger.error(msg)
        raise ValueError(msg)

    # Validação da fonte de dados (aceita str ou list, case-insensitive)
    valid_sources = [
        "nasa_power",
        "openmeteo_forecast",
        "data fusion",
    ]

    # Normalize input to list of lower-case strings
    if isinstance(data_source, list):
        requested = [str(s).lower() for s in data_source]
    else:
        requested = [str(data_source).lower()]

    # Validate requested sources
    for req in requested:
        if req not in valid_sources:
            msg = f"Fonte inválida: {data_source}. Use: {', '.join(valid_sources)}"
            logger.error(msg)
            raise ValueError(msg)

    # Define sources to query
    if "data fusion" in requested:
        sources = ["nasa_power", "openmeteo_forecast"]
        logger.info(
            "Data Fusion selecionada, coletando dados de múltiplas fontes (NASA POWER + OpenMeteo Forecast)."
        )
    else:
        sources = requested
        logger.info(f"Fonte(s) selecionada(s): {sources}")

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
        # Inicializa variáveis
        weather_df = None
        fetch_warnings = []

        try:
            if source == "nasa_power":
                api = NasaPowerAPI(
                    start=data_inicial_formatted,
                    end=data_final_adjusted,
                    long=longitude,
                    lat=latitude
                )
                weather_df, fetch_warnings = api.get_weather_sync()
                logger.info("NASA POWER: obtidos dados para (%s, %s)", 
                          latitude, longitude)

            elif source == "openmeteo_forecast":
                api = OpenMeteoForecastAPI(
                    start=data_inicial_formatted,
                    end=data_final_adjusted,
                    long=longitude,
                    lat=latitude
                )
                weather_df, fetch_warnings = api.get_weather_sync()
                logger.info("Open-Meteo Forecast: obtidos dados para (%s, %s)", 
                          latitude, longitude)

        except Exception as e:
            logger.error("%s: erro ao baixar dados: %s", source, str(e))
            warnings_list.append(
                f"{source}: erro ao baixar dados: {str(e)}"
            )
            continue

            # Valida DataFrame
            if weather_df is None or weather_df.empty:
                msg = (
                    f"Nenhum dado obtido de {source} para ({latitude}, {longitude}) "
                    f"entre {data_inicial} e {data_final}"
                )
                logger.warning(msg)
                warnings_list.append(msg)
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

            # Verifica quantidade de dados
            dias_retornados = (
                weather_df.index.max() - weather_df.index.min()
            ).days + 1
            if dias_retornados < period_days:
                msg = (
                    f"{source}: obtidos {dias_retornados} dias "
                    f"(solicitados: {period_days})"
                )
                warnings_list.append(msg)

            # Verifica dados faltantes
            perc_faltantes = weather_df.isna().mean() * 100
            nomes_variaveis = {
                "ALLSKY_SFC_SW_DWN": "Radiação Solar (MJ/m²/dia)",
                "PRECTOTCORR": "Precipitação Total (mm)",
                "T2M_MAX": "Temperatura Máxima (°C)",
                "T2M_MIN": "Temperatura Mínima (°C)",
                "T2M": "Temperatura Média (°C)",
                "RH2M": "Umidade Relativa (%)",
                "WS2M": "Velocidade do Vento (m/s)",
            }
            
            for nome_var, porcentagem in perc_faltantes.items():
                if porcentagem > 25:
                    var_portugues = nomes_variaveis[nome_var]
                    msg = (
                        f"{source}: {porcentagem:.1f}% faltantes em "
                        f"{var_portugues}. Será feita imputação."
                    )
                    warnings_list.append(msg)

            dfs.append(weather_df)
            logger.debug("%s: DataFrame obtido\n%s", source, weather_df)

    # Realiza fusão se necessário
    if data_source == "Data Fusion":
        if len(dfs) < 2:
            msg = "São necessárias pelo menos duas fontes válidas para fusão"
            logger.error(msg)
            raise ValueError(msg)
        
        try:
            # Converte DataFrames para dicionários preservando os índices
            df_dicts = []
            for df in dfs:
                df_dict = {}
                for idx, row in df.iterrows():
                    key = idx.strftime("%Y-%m-%d %H:%M:%S")
                    df_dict[key] = row.to_dict()
                df_dicts.append(df_dict)
            
            # Executa fusão
            task = data_fusion.delay(df_dicts)
            weather_data_dict, fusion_warnings = task.get(timeout=10)
            warnings_list.extend(fusion_warnings)
            
            # Converte resultado para DataFrame
            weather_data = pd.DataFrame.from_dict(
                weather_data_dict, 
                orient='index'
            )
            weather_data.index = pd.to_datetime(weather_data.index)
            logger.info("Fusão de dados concluída com sucesso")
            
        except Exception as e:
            msg = f"Erro na fusão de dados: {str(e)}"
            logger.error(msg)
            raise ValueError(msg)
    else:
        if not dfs:
            msg = "Nenhuma fonte forneceu dados válidos"
            logger.error(msg)
            raise ValueError(msg)
        weather_data = dfs[0]

    # Validação final
    colunas_esperadas = [
        "T2M_MAX", "T2M_MIN", "T2M", "RH2M", "WS2M",
        "ALLSKY_SFC_SW_DWN", "PRECTOTCORR"
    ]
    colunas_faltantes = set(colunas_esperadas) - set(weather_data.columns)
    if colunas_faltantes:
        msg = f"Colunas ausentes: {', '.join(colunas_faltantes)}"
        logger.error(msg)
        raise ValueError(msg)

    logger.info("Dados finais obtidos com sucesso")
    logger.debug("DataFrame final:\n%s", weather_data)
    return weather_data, warnings_list