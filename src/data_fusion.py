"""
Módulo de fusão de dados meteorológicos usando Filtro de Kalman Ensemble.

Este módulo implementa:
- Fusão de dados de múltiplas fontes
- Tratamento de dados faltantes
- Correção de viés
- Controle de qualidade
"""

import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from celery import shared_task
from loguru import logger
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime

# Configuração do logging
logger.add(
    "./logs/data_fusion.log",
    rotation="10 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# Constantes
REQUIRED_COLUMNS = [
    "T2M_MAX", "T2M_MIN", "T2M", "RH2M", 
    "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR"
]


@shared_task(bind=True, name='src.data_fusion.data_fusion')
def data_fusion(
    self,
    dfs: List[dict],
    ensemble_size: int = 50,
    inflation_factor: float = 1.02
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Realiza a fusão de dados meteorológicos usando Filtro de Kalman Ensemble.

    Args:
        dfs: Lista de dicionários com dados de diferentes fontes
        ensemble_size: Tamanho do ensemble para o filtro
        inflation_factor: Fator de inflação para evitar subestimação da variância

    Returns:
        Tuple[Dict[str, Any], List[str]]: Estado analisado após fusão e avisos.
    
    Raises:
        ValueError: Se os dados de entrada forem inválidos
    """
    """
    Realiza a fusão de dados com Kalman Ensemble para múltiplas fontes.

    Args:
        dfs: Lista de dicionários contendo DataFrames com dados climáticos.
        ensemble_size: Número de membros do ensemble (padrão: 50).
        inflation_factor: Fator de inflação (padrão: 1.02).

    Returns:
        Tuple[dict, List[str]]: Dicionário com o estado analisado após fusão e lista de avisos.

    Example:
        >>> dfs = [df1.to_dict(), df2.to_dict()]
        >>> result, warnings = data_fusion(dfs)
    """
    warnings = []
    dataframes = []
    
    try:
        logger.info("Iniciando fusão de dados com Kalman Ensemble")
        
        # Validação inicial dos dados
        if len(dfs) < 2:
            msg = "São necessárias pelo menos duas fontes de dados para fusão"
            logger.warning(msg)
            if len(dfs) == 1:
                return dfs[0], [msg]
            raise ValueError("Nenhuma fonte de dados fornecida")

        # Conversão e validação dos DataFrames
        for i, df_dict in enumerate(dfs):
            try:
                df = pd.DataFrame(df_dict)
                
                # Validar índice temporal
                if not pd.api.types.is_datetime64_any_dtype(df.index):
                    msg = f"Fonte {i}: Índice deve ser datetime"
                    raise ValueError(msg)
                
                # Verificar colunas necessárias
                missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
                if missing_cols:
                    cols_str = ", ".join(missing_cols)
                    msg = f"Fonte {i}: Faltam colunas: {cols_str}"
                    raise ValueError(msg)
                
                dataframes.append(df)
                logger.info("Fonte %d: Dados validados", i)
                
            except Exception as e:
                msg = f"Erro na fonte {i}: {str(e)}"
                logger.error(msg)
                raise ValueError(msg)

        # Validação de dimensões e alinhamento temporal
        shapes = [df.shape for df in dataframes]
        if len(set(shapes)) > 1:
            msg = "Dimensões incompatíveis entre fontes"
            logger.warning(msg)
            warnings.append(msg)
            
            # Usar interseção de índices
            common_index = dataframes[0].index
            for df in dataframes[1:]:
                common_index = common_index.intersection(df.index)
            
            if len(common_index) == 0:
                raise ValueError("Sem período em comum")
                
            dataframes = [df.loc[common_index] for df in dataframes]
            n_periods = len(common_index)
            logger.info("Alinhados %d períodos", n_periods)

        # Pré-processamento dos dados
        imputer = KNNImputer(n_neighbors=5)
        for i, df in enumerate(dataframes):
            missing_mask = df.isna()
            if missing_mask.any().any():
                df.loc[:, :] = imputer.fit_transform(df)
                n_missing = int(missing_mask.sum().sum())
                msg = f"Fonte {i}: {n_missing} valores imputados"
                warnings.append(msg)
                logger.info("Fonte %d: Imputação OK", i)

        # Fusão de dados com Kalman Ensemble
        n_times, n_vars = dataframes[0].shape
        
        # Criar ensemble inicial
        forecast = np.mean([df.to_numpy() for df in dataframes], axis=0)
        ensemble = np.array([
            forecast + np.random.normal(0, 0.1, forecast.shape)
            for _ in range(ensemble_size)
        ])

        # Inflação do ensemble
        ensemble_mean = np.mean(ensemble, axis=0)
        ensemble_pert = ensemble - ensemble_mean
        ensemble = ensemble_mean + inflation_factor * ensemble_pert

        # Estado analisado
        analyzed_state = np.zeros((n_times, n_vars))
        H = np.eye(n_vars)  # Matriz de observação
        R = np.eye(n_vars) * 0.1  # Covariância das observações
        
        # Processamento por passo de tempo
        for t in range(n_times):
            # Média e perturbações do ensemble
            forecast_mean = np.mean(ensemble[:, t, :], axis=0)
            forecast_pert = ensemble[:, t, :] - forecast_mean
            
            # Matriz de covariância do forecast
            P = np.cov(forecast_pert.T) * inflation_factor
            
            # Inovação e ganho de Kalman
            obs = dataframes[0].iloc[t].to_numpy()
            innov = obs - np.dot(H, forecast_mean)
            K = P @ H.T @ np.linalg.inv(H @ P @ H.T + R)
            
            # Atualização do estado
            analyzed_state[t] = forecast_mean + K @ innov
            
            # Atualização do ensemble para próximo passo
            if t < n_times - 1:
                ensemble_update = ensemble_mean[t+1] + forecast_pert
                ensemble[:, t+1, :] = ensemble_update
        
        # Resultado final
        result_df = pd.DataFrame(
            analyzed_state,
            index=dataframes[0].index,
            columns=REQUIRED_COLUMNS
        )
        
        logger.info("Fusão de dados concluída com sucesso")
        
        # Converter para o formato de retorno esperado
        result_dict: Dict[str, Any] = {}
        for idx, row in result_df.iterrows():
            # Garantir que o índice é datetime
            if isinstance(idx, (pd.Timestamp, datetime)):
                key = idx.strftime("%Y-%m-%d %H:%M:%S")
            else:
                key = str(idx)
            result_dict[key] = row.to_dict()
        
        return result_dict, warnings

    except Exception as e:
        msg = f"Erro na fusão de dados: {str(e)}"
        logger.exception(msg)
        warnings.append(msg)
        raise ValueError(msg)
