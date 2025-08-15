import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from celery import shared_task
from loguru import logger
from typing import List, Tuple

@shared_task
def data_fusion(dfs: List[dict], ensemble_size: int = 50, inflation_factor: float = 1.02) -> Tuple[dict, List[str]]:
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
    try:
        logger.info("Iniciando fusão de dados com Kalman Ensemble")
        
        if len(dfs) < 2:
            warnings.append("At least two data sources are required for fusion.")
            logger.error(warnings[-1])
            raise ValueError(warnings[-1])

        # Converter dicionários para DataFrames
        dataframes = [pd.DataFrame(df) for df in dfs]
        
        # Validar índices e colunas
        for i, df in enumerate(dataframes):
            if not pd.api.types.is_datetime64_any_dtype(df.index):
                warnings.append(f"DataFrame {i} must have a datetime index.")
                logger.error(warnings[-1])
                raise ValueError(warnings[-1])
            if not all(col in df.columns for col in ["T2M_MAX", "T2M_MIN", "T2M", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR"]):
                warnings.append(f"DataFrame {i} is missing required columns.")
                logger.error(warnings[-1])
                raise ValueError(warnings[-1])
        
        # Verificar compatibilidade de dimensões
        n_times = dataframes[0].shape[0]
        n_vars = dataframes[0].shape[1]
        for i, df in enumerate(dataframes[1:], 1):
            if df.shape[0] != n_times or df.shape[1] != n_vars:
                warnings.append(f"DataFrame {i} has incompatible dimensions with DataFrame 0.")
                logger.error(warnings[-1])
                raise ValueError(warnings[-1])
        
        # Combinar DataFrames (média inicial para previsão e observação)
        combined_df = pd.concat(dataframes, axis=1, keys=range(len(dataframes)))
        forecast_data_np = combined_df.groupby(level=1, axis=1).mean().to_numpy()
        observation_data_np = dataframes[0].to_numpy()  # Usa o primeiro DataFrame como observação inicial

        # Ajustar dimensões para ensemble
        forecast_data_np = np.tile(forecast_data_np[:, :, np.newaxis], (1, 1, ensemble_size))
        n_ensemble = forecast_data_np.shape[2]
        
        # Imputação com kNN
        imputer = KNNImputer(n_neighbors=5)
        forecast_flat = forecast_data_np.reshape(-1, n_vars)
        observation_flat = observation_data_np.reshape(-1, n_vars)
        forecast_imputed = imputer.fit_transform(forecast_flat)
        observation_imputed = imputer.transform(observation_flat)
        forecast_data_np = forecast_imputed.reshape(n_times, n_vars, ensemble_size)
        observation_data_np = observation_imputed.reshape(n_times, n_vars)
        
        # Validar valores imputados
        for col in ["ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "WS2M"]:
            if (forecast_data_np[:, dataframes[0].columns.get_loc(col), :] < 0).any():
                warnings.append(f"Negative values detected in {col} after imputation.")
                logger.warning(warnings[-1])
        
        # Inicializar estado analisado
        analyzed_state = np.zeros((n_times, n_vars))
        
        for t in range(n_times):
            forecast_mean = np.mean(forecast_data_np[t], axis=1)
            forecast_pert = forecast_data_np[t] - forecast_mean[:, np.newaxis]
            P = np.cov(forecast_pert) * inflation_factor
            obs_pert = observation_data_np[t] + np.random.normal(0, 0.1, (n_vars, n_ensemble))
            H = np.eye(n_vars)
            innov = obs_pert - np.dot(H, forecast_mean)
            K = np.dot(P, H.T) @ np.linalg.inv(np.dot(H, np.dot(P, H.T)) + 0.1 * np.eye(n_vars))
            analyzed_state[t] = forecast_mean + np.dot(K, innov.mean(axis=1))
        
        # Retornar como dicionário
        result_df = pd.DataFrame(analyzed_state, index=dataframes[0].index, columns=dataframes[0].columns)
        logger.info("Fusão de dados concluída com sucesso")
        return result_df.to_dict(), warnings
    except Exception as e:
        warnings.append(f"Erro na fusão de dados: {str(e)}")
        logger.error(warnings[-1])
        return {}, warnings