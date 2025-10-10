"""
OpenMeteo Client específico para previsões MATOPIBA.

Este módulo implementa:
- Busca de previsões meteorológicas para 337 cidades MATOPIBA
- Requisições em lote para otimização
- Retorno de variáveis para cálculo ETo + ETo Open-Meteo (validação)
- Conformidade com licença CC-BY-NC 4.0 (apenas visualização)

Autor: EVAonline Team
Data: 2025-10-09
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
from loguru import logger
from requests.exceptions import RequestException

# Configuração do logging
logger.add(
    "./logs/openmeteo_matopiba.log",
    rotation="10 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# Constantes
CITIES_FILE = Path(__file__).parent.parent.parent.parent / "data" / "csv" / "CITIES_MATOPIBA_337.csv"
OPENMETEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
BATCH_SIZE = 50  # Requisições em lote para otimizar
REQUEST_DELAY = 2.0  # Delay entre lotes (segundos) para respeitar rate limits


class OpenMeteoMatopibaClient:
    """
    Cliente Open-Meteo para previsões MATOPIBA.
    
    ⚠️ IMPORTANTE: Licença CC-BY-NC 4.0
    - Uso apenas para visualização (MATOPIBA map)
    - NÃO usar em fusão de dados (data_fusion.py)
    - NÃO usar em downloads diretos pelo usuário
    - Permitido apenas para interface web (visualização online)
    
    Attributes:
        cities_df: DataFrame com 337 cidades MATOPIBA
        forecast_days: Número de dias de previsão (padrão: 2 = hoje + amanhã)
    """
    
    def __init__(self, forecast_days: int = 2):
        """
        Inicializa cliente Open-Meteo para MATOPIBA.
        
        Args:
            forecast_days: Número de dias de previsão (padrão: 2)
        
        Raises:
            FileNotFoundError: Se arquivo de cidades não for encontrado
            ValueError: Se arquivo de cidades estiver vazio ou inválido
        """
        self.forecast_days = forecast_days
        self.cities_df = self._load_cities()
        logger.info(
            "OpenMeteo MATOPIBA Client inicializado: %d cidades, %d dias",
            len(self.cities_df), forecast_days
        )
    
    def _load_cities(self) -> pd.DataFrame:
        """
        Carrega lista de 337 cidades MATOPIBA.
        
        Returns:
            DataFrame com colunas: CODE_CITY, CITY, UF, LATITUDE, LONGITUDE, HEIGHT
        
        Raises:
            FileNotFoundError: Se arquivo não existir
            ValueError: Se arquivo estiver vazio ou com colunas incorretas
        """
        if not CITIES_FILE.exists():
            msg = f"Arquivo de cidades não encontrado: {CITIES_FILE}"
            logger.error(msg)
            raise FileNotFoundError(msg)
        
        try:
            df = pd.read_csv(CITIES_FILE, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(CITIES_FILE, encoding='latin-1')
        
        required_cols = ['CODE_CITY', 'CITY', 'UF', 'LATITUDE', 'LONGITUDE', 'HEIGHT']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            msg = f"Colunas ausentes no arquivo de cidades: {missing_cols}"
            logger.error(msg)
            raise ValueError(msg)
        
        if df.empty:
            msg = "Arquivo de cidades está vazio"
            logger.error(msg)
            raise ValueError(msg)
        
        logger.info("Carregadas %d cidades MATOPIBA", len(df))
        return df
    
    def _build_batch_url(
        self,
        latitudes: List[float],
        longitudes: List[float]
    ) -> str:
        """
        Constrói URL para requisição em lote Open-Meteo com dados HORÁRIOS.
        
        Args:
            latitudes: Lista de latitudes
            longitudes: Lista de longitudes
        
        Returns:
            URL completa com parâmetros
        """
        # Variáveis HORÁRIAS para ETo Penman-Monteith + validação
        # ⚠️ Dados HORÁRIOS (não diários) para cálculo preciso
        hourly_vars = [
            "temperature_2m",                # Temp a 2m (°C)
            "relative_humidity_2m",          # RH a 2m (%)
            "dew_point_2m",                  # Td (°C) - prioritário p/ ea
            "wind_speed_10m",                # Vento 10m (m/s)
            "surface_pressure",              # Pressão (hPa)
            "shortwave_radiation",           # Radiação (W/m²)
            "cloud_cover",                   # Nuvens (%) - ajuste Rnl
            "vapour_pressure_deficit",       # VPD (kPa) - validação
            "precipitation",                 # Precip (mm)
            "precipitation_probability",     # Prob precip (%)
            "et0_fao_evapotranspiration"     # ETo OM (mm) - validação
        ]
        
        # Formatar coordenadas para API (aceita múltiplas localizações)
        lat_str = ",".join([f"{lat:.4f}" for lat in latitudes])
        lon_str = ",".join([f"{lon:.4f}" for lon in longitudes])
        
        # Construir URL com dados horários
        params = {
            "latitude": lat_str,
            "longitude": lon_str,
            "hourly": ",".join(hourly_vars),
            "models": "best_match",          # Usa melhor modelo disponível
            "forecast_days": self.forecast_days,
            "timezone": "UTC"                # UTC para consistência com cálculos solares
        }
        
        # Montar query string
        query_parts = [f"{k}={v}" for k, v in params.items()]
        url = f"{OPENMETEO_BASE_URL}?{'&'.join(query_parts)}"
        
        return url
    
    def _fetch_batch(
        self,
        batch_df: pd.DataFrame
    ) -> Tuple[Dict[str, Dict], List[str]]:
        """
        Busca dados de previsão para um lote de cidades.
        
        Args:
            batch_df: DataFrame com cidades do lote
        
        Returns:
            Tuple[Dict, List]: Dados por cidade e lista de avisos
        """
        warnings = []
        results = {}
        
        latitudes = batch_df['LATITUDE'].tolist()
        longitudes = batch_df['LONGITUDE'].tolist()
        city_codes = batch_df['CODE_CITY'].tolist()
        
        url = self._build_batch_url(latitudes, longitudes)
        
        try:
            logger.debug("Requisição Open-Meteo: %d cidades", len(batch_df))
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Processar resposta
            # Open-Meteo retorna array de resultados (um por localização)
            if isinstance(data, list):
                # Múltiplas localizações
                for i, city_data in enumerate(data):
                    if i < len(city_codes):
                        city_code = str(city_codes[i])
                        results[city_code] = self._parse_city_data(
                            city_data, batch_df.iloc[i]
                        )
            else:
                # Resposta única (formato antigo ou erro)
                if 'latitude' in data and isinstance(data['latitude'], (list, tuple)):
                    # Múltiplas localizações em formato único
                    for i in range(len(data['latitude'])):
                        city_code = str(city_codes[i])
                        city_specific_data = {
                            'latitude': data['latitude'][i],
                            'longitude': data['longitude'][i],
                            'daily': {
                                key: [val[i]] if isinstance(val, list) else val
                                for key, val in data.get('daily', {}).items()
                            }
                        }
                        results[city_code] = self._parse_city_data(
                            city_specific_data, batch_df.iloc[i]
                        )
                else:
                    # Resposta única (1 localização)
                    city_code = str(city_codes[0])
                    results[city_code] = self._parse_city_data(
                        data, batch_df.iloc[0]
                    )
            
            logger.info("Lote processado: %d/%d cidades", len(results), len(batch_df))
            
        except RequestException as e:
            msg = f"Erro HTTP na requisição Open-Meteo: {e}"
            logger.error(msg)
            warnings.append(msg)
        except Exception as e:
            msg = f"Erro ao processar resposta Open-Meteo: {e}"
            logger.error(msg)
            warnings.append(msg)
        
        return results, warnings
    
    def _parse_city_data(
        self,
        api_data: Dict,
        city_info: pd.Series
    ) -> Dict:
        """
        Parse dados da API para formato padrão EVAonline.
        
        ⚠️ IMPORTANTE: Retorna dados HORÁRIOS brutos + agregados diários
        - hourly_data: Para cálculo ETo EVAonline (eto_hourly.py)
        - forecast: Dados diários agregados (para validação/compatibilidade)
        
        Args:
            api_data: Dados da API Open-Meteo
            city_info: Informações da cidade (Series do DataFrame)
        
        Returns:
            Dicionário com city_info, hourly_data (bruto) e forecast (agregado)
        """
        # ⚠️ MUDANÇA: Agora processamos dados HORÁRIOS
        hourly = api_data.get('hourly', {})
        time = hourly.get('time', [])
        
        if not time:
            logger.warning("Sem dados horários para cidade %s", city_info['CITY'])
            return {'city_info': {}, 'hourly_data': {}, 'forecast': {}}
        
        # Extrair variáveis horárias (com fallback para None)
        temp = hourly.get('temperature_2m', [None] * len(time))
        rh = hourly.get('relative_humidity_2m', [None] * len(time))
        dew_point = hourly.get('dew_point_2m', [None] * len(time))
        ws = hourly.get('wind_speed_10m', [None] * len(time))
        pressure = hourly.get('surface_pressure', [None] * len(time))
        radiation = hourly.get('shortwave_radiation', [None] * len(time))
        cloud = hourly.get('cloud_cover', [None] * len(time))
        vpd = hourly.get('vapour_pressure_deficit', [None] * len(time))
        precip = hourly.get('precipitation', [None] * len(time))
        precip_prob = hourly.get(
            'precipitation_probability', [None] * len(time)
        )
        eto = hourly.get('et0_fao_evapotranspiration', [None] * len(time))
        
        # Criar DataFrame para facilitar agregação
        df = pd.DataFrame({
            'time': pd.to_datetime(time),
            'temp': temp,
            'rh': rh,
            'dew_point': dew_point,
            'ws': ws,
            'pressure': pressure,
            'radiation': radiation,
            'cloud': cloud,
            'vpd': vpd,
            'precip': precip,
            'precip_prob': precip_prob,
            'eto': eto
        })
        
        # ===================================================================
        # 1) DADOS HORÁRIOS BRUTOS (para calculate_eto_hourly)
        # ===================================================================
        hourly_data_dict = {
            'time': time,
            'temperature_2m': temp,
            'relative_humidity_2m': rh,
            'dew_point_2m': dew_point,
            'wind_speed_10m': ws,
            'surface_pressure': pressure,
            'shortwave_radiation': radiation,
            'cloud_cover': cloud,
            'vapour_pressure_deficit': vpd,
            'precipitation': precip,
            'precipitation_probability': precip_prob,
            'et0_fao_evapotranspiration': eto
        }
        
        # ===================================================================
        # 2) AGREGAÇÃO DIÁRIA (para compatibilidade/validação)
        # ===================================================================
        # Extrair data (sem hora)
        df['date'] = df['time'].dt.date
        
        # Agregar por dia
        daily_data = df.groupby('date').agg({
            'temp': ['min', 'max', 'mean'],
            'rh': 'mean',
            'ws': 'mean',
            # W/m² → MJ/m²/dia: soma * 3600s/h / 1e6
            'radiation': lambda x: np.sum(x) * 3600 / 1_000_000,
            'precip': 'sum',
            'precip_prob': 'mean',
            'eto': 'sum'  # Somar ETo horária para obter diária
        }).reset_index()
        
        # Renomear colunas
        daily_data.columns = ['date', 'T2M_MIN', 'T2M_MAX', 'T2M',
                              'RH2M', 'WS2M', 'ALLSKY_SFC_SW_DWN',
                              'PRECTOTCORR', 'PREC_PROB', 'ETo_OpenMeteo']
        
        # Construir resultado
        result = {
            'city_info': {
                'code': str(city_info['CODE_CITY']),
                'name': city_info['CITY'],
                'uf': city_info['UF'],
                'latitude': float(city_info['LATITUDE']),
                'longitude': float(city_info['LONGITUDE']),
                'elevation': float(city_info['HEIGHT'])
            },
            'hourly_data': hourly_data_dict,  # NOVO: dados horários brutos
            'forecast': {}
        }
        
        # Adicionar dados por dia
        for _, row in daily_data.iterrows():
            date_str = str(row['date'])
            result['forecast'][date_str] = {
                'T2M_MAX': float(row['T2M_MAX']),
                'T2M_MIN': float(row['T2M_MIN']),
                'T2M': float(row['T2M']),
                'RH2M': float(row['RH2M']),
                'WS2M': float(row['WS2M']),
                'ALLSKY_SFC_SW_DWN': float(row['ALLSKY_SFC_SW_DWN']),
                'PRECTOTCORR': float(row['PRECTOTCORR']),
                'PREC_PROB': float(row['PREC_PROB']),
                'ETo_OpenMeteo': float(row['ETo_OpenMeteo'])
            }
        
        return result
    
    def get_forecasts_all_cities(self) -> Tuple[Dict[str, Dict], List[str]]:
        """
        Busca previsões para todas as 337 cidades MATOPIBA.
        
        Implementa:
        - Requisições em lote (BATCH_SIZE cidades por vez)
        - Rate limiting (delay entre lotes)
        - Tratamento de erros por lote
        
        Returns:
            Tuple[Dict, List]: Dados por cidade e lista de avisos
        
        Example:
            >>> client = OpenMeteoMatopibaClient()
            >>> forecasts, warnings = client.get_forecasts_all_cities()
            >>> len(forecasts)  # 337 cidades
            337
        """
        logger.info("Iniciando busca de previsões para 337 cidades MATOPIBA")
        all_results = {}
        all_warnings = []
        
        # Dividir em lotes
        n_cities = len(self.cities_df)
        n_batches = (n_cities + BATCH_SIZE - 1) // BATCH_SIZE
        
        for batch_idx in range(n_batches):
            start_idx = batch_idx * BATCH_SIZE
            end_idx = min((batch_idx + 1) * BATCH_SIZE, n_cities)
            
            batch_df = self.cities_df.iloc[start_idx:end_idx]
            
            logger.info(
                "Processando lote %d/%d (%d cidades)",
                batch_idx + 1, n_batches, len(batch_df)
            )
            
            # Buscar dados do lote
            batch_results, batch_warnings = self._fetch_batch(batch_df)
            all_results.update(batch_results)
            all_warnings.extend(batch_warnings)
            
            # Rate limiting (exceto no último lote)
            if batch_idx < n_batches - 1:
                logger.debug("Aguardando %.1fs antes do próximo lote", REQUEST_DELAY)
                sleep(REQUEST_DELAY)
        
        success_rate = (len(all_results) / n_cities) * 100
        logger.info(
            "Busca concluída: %d/%d cidades (%.1f%%)",
            len(all_results), n_cities, success_rate
        )
        
        if success_rate < 90:
            msg = f"Taxa de sucesso baixa: {success_rate:.1f}%"
            all_warnings.append(msg)
            logger.warning(msg)
        
        return all_results, all_warnings
    
    def get_forecast_single_city(
        self,
        city_code: str
    ) -> Tuple[Optional[Dict], List[str]]:
        """
        Busca previsão para uma cidade específica.
        
        Args:
            city_code: Código IBGE da cidade
        
        Returns:
            Tuple[Dict, List]: Dados da cidade e avisos
        """
        warnings = []
        
        # Encontrar cidade
        city_row = self.cities_df[
            self.cities_df['CODE_CITY'].astype(str) == str(city_code)
        ]
        
        if city_row.empty:
            msg = f"Cidade não encontrada: {city_code}"
            logger.warning(msg)
            warnings.append(msg)
            return None, warnings
        
        # Buscar dados
        batch_results, batch_warnings = self._fetch_batch(city_row)
        warnings.extend(batch_warnings)
        
        city_data = batch_results.get(str(city_code))
        if not city_data:
            msg = f"Nenhum dado retornado para cidade: {city_code}"
            warnings.append(msg)
            logger.warning(msg)
        
        return city_data, warnings


# Funções auxiliares para uso direto

def fetch_matopiba_forecasts() -> Tuple[Dict[str, Dict], List[str]]:
    """
    Função auxiliar para buscar previsões MATOPIBA (uso em tasks Celery).
    
    Returns:
        Tuple[Dict, List]: Dados por cidade e avisos
    
    Example:
        >>> forecasts, warnings = fetch_matopiba_forecasts()
        >>> print(f"Cidades: {len(forecasts)}")
    """
    client = OpenMeteoMatopibaClient(forecast_days=2)
    return client.get_forecasts_all_cities()


def fetch_matopiba_city_forecast(city_code: str) -> Tuple[Optional[Dict], List[str]]:
    """
    Função auxiliar para buscar previsão de uma cidade específica.
    
    Args:
        city_code: Código IBGE da cidade
    
    Returns:
        Tuple[Dict, List]: Dados da cidade e avisos
    """
    client = OpenMeteoMatopibaClient(forecast_days=2)
    return client.get_forecast_single_city(city_code)


if __name__ == "__main__":
    # Teste rápido
    logger.info("=== TESTE: OpenMeteo MATOPIBA Client ===")
    
    client = OpenMeteoMatopibaClient()
    
    # Testar uma cidade
    logger.info("Testando busca para cidade única...")
    city_data, warnings = client.get_forecast_single_city("1700251")  # Abreulândia, TO
    
    if city_data:
        logger.info("✅ Sucesso! Cidade: %s", city_data['city_info']['name'])
        logger.info("Dias previstos: %s", list(city_data['forecast'].keys()))
    else:
        logger.error("❌ Falha ao buscar dados")
    
    if warnings:
        logger.warning("Avisos: %s", warnings)
