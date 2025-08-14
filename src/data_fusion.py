import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from celery import Celery
from loguru import logger

app = Celery("processing", broker="redis://redis:6379/0", backend="redis://redis:6379/0")


@app.task
def data_fusion(forecast_data: dict, observation_data: dict, ensemble_size: int = 50, inflation_factor: float = 1.02) -> dict:
    """
    Realiza a fusão de dados com Kalman Ensemble.
    
    Parâmetros:
    - forecast_data: Dicionário com dados de previsão
    - observation_data: Dicionário com dados de observação
    - ensemble_size: Número de membros do ensemble (padrão: 50)
    - inflation_factor: Fator de inflação (padrão: 1.02)
    
    Retorna:
    - Dicionário com o estado analisado após fusão
    """
    try:
        # Converter dicionários para DataFrames
        forecast_df = pd.DataFrame(forecast_data)
        observation_df = pd.DataFrame(observation_data)
        
        # Verificar dimensões
        n_times, n_vars = observation_df.shape
        if forecast_df.shape[0] != n_times or forecast_df.shape[1] != n_vars:
            logger.error("Dimensões de forecast_data e observation_data não compatíveis")
            raise ValueError("Dimensões de forecast_data e observation_data não compatíveis")
        
        # Converter para numpy arrays
        forecast_data_np = forecast_df.to_numpy()
        observation_data_np = observation_df.to_numpy()
        
        # Ajustar dimensões para ensemble
        if len(forecast_data_np.shape) == 2:
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
        result_df = pd.DataFrame(analyzed_state, columns=forecast_df.columns)
        logger.info("Fusão de dados concluída com sucesso")
        return result_df.to_dict()
    except Exception as e:
        logger.error(f"Erro na fusão de dados: {str(e)}")
        raise