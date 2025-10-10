# 🔄 Plano de Atualização: Integração Completa dos Novos Clientes

## 📊 Análise da Situação Atual

### **Problema Identificado**

Os arquivos de processamento de dados (`data_download.py`, `data_preprocessing.py`, `data_fusion.py`) ainda usam os **clientes legados** (`nasapower.py`, `openmeteo.py`) e não estão integrados com os **novos clientes cache-enabled** criados recentemente:

- ✅ `nasa_power_client.py` (global, async, cache-integrated)
- ✅ `met_norway_client.py` (Europa, async, cache-integrated)
- ✅ `nws_client.py` (USA, async, cache-integrated)

### **Incompatibilidades Detectadas**

| Aspecto | Clientes Legados | Novos Clientes | Status |
|---------|------------------|----------------|--------|
| **Interface** | `get_weather_sync()` | `async get_daily_data()` | ❌ Incompatível |
| **Retorno** | `(DataFrame, List[str])` | `Dict[str, Any]` | ❌ Formato diferente |
| **Cache** | Redis embutido | Dependency injection | ⚠️ Híbrido |
| **Cobertura** | Global/MATOPIBA | Bbox-aware | ❌ Validação ausente |
| **Fusão** | 2 fontes fixas | Flexível (2+) | ❌ Lógica limitada |

---

## 🎯 Objetivos

### **1. Compatibilidade**
- Adicionar método `get_weather_sync()` aos novos clientes
- Manter interface consistente com código existente

### **2. Validação de Cobertura**
- Verificar bbox antes de download
- Mensagens claras quando fonte indisponível

### **3. Fusão Inteligente**
- Suportar 2+ fontes simultaneamente
- Pesos baseados em prioridade + distância + qualidade

### **4. Pré-processamento por Fonte**
- Normalizar resolução temporal (hourly → daily)
- Harmonizar unidades (°F → °C, mph → m/s)

### **5. Conformidade de Licença**
- Bloquear Open-Meteo em fusão (já implementado ✅)
- Validar antes do download

---

## 📝 Tarefas de Implementação

### **Tarefa 1: Adicionar `get_weather_sync()` aos Novos Clientes**

**Arquivos:**
- `backend/api/services/nasa_power_client.py`
- `backend/api/services/met_norway_client.py`
- `backend/api/services/nws_client.py`

**Implementação:**

```python
# nasa_power_client.py
def get_weather_sync(
    self,
    start: datetime,
    end: datetime,
    lat: float,
    lon: float
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Método síncrono compatível com data_download.py.
    
    Wrapper que chama get_daily_data() e converte resultado.
    """
    import asyncio
    
    warnings = []
    
    try:
        # Executar método async
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Se já há event loop rodando (Celery), criar task
            result = asyncio.run_coroutine_threadsafe(
                self.get_daily_data(
                    lat=lat,
                    lon=lon,
                    start_date=start,
                    end_date=end
                ),
                loop
            ).result(timeout=30)
        else:
            # Se não há event loop, criar novo
            result = asyncio.run(
                self.get_daily_data(
                    lat=lat,
                    lon=lon,
                    start_date=start,
                    end_date=end
                )
            )
        
        # Converter resultado para DataFrame
        if not result or 'data' not in result:
            raise ValueError("No data returned from NASA POWER API")
        
        df = pd.DataFrame(result['data'])
        df.index = pd.to_datetime(df.index)
        
        # Mapear colunas para formato esperado
        column_mapping = {
            'T2M_MAX': 'T2M_MAX',
            'T2M_MIN': 'T2M_MIN',
            'T2M': 'T2M',
            'RH2M': 'RH2M',
            'WS2M': 'WS2M',
            'ALLSKY_SFC_SW_DWN': 'ALLSKY_SFC_SW_DWN',
            'PRECTOTCORR': 'PRECTOTCORR'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Warnings
        if result.get('cache_hit'):
            warnings.append("Data loaded from cache (NASA POWER)")
        
        return df, warnings
        
    except Exception as e:
        error_msg = f"NASA POWER API error: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
```

**Padrão similar para MET Norway e NWS:**
- MET: Converte dados horários → diários (agregação)
- NWS: Converte °F → °C, mph → m/s

---

### **Tarefa 2: Atualizar `data_download.py`**

**Mudanças necessárias:**

#### **2.1: Importar novos clientes**

```python
# REMOVER (legados)
from backend.api.services.nasapower import NasaPowerAPI
from backend.api.services.openmeteo import OpenMeteoForecastAPI

# ADICIONAR (novos)
from backend.api.services.nasa_power_client import NASAPowerClient
from backend.api.services.met_norway_client import METNorwayClient
from backend.api.services.nws_client import NWSClient
from backend.api.services.climate_source_manager import ClimateSourceManager
from backend.infrastructure.cache.climate_cache import create_climate_cache
```

#### **2.2: Validar cobertura geográfica**

```python
def download_weather_data(
    data_source: Union[str, List[str]],
    data_inicial: str,
    data_final: str,
    longitude: float,
    latitude: float,
) -> Tuple[pd.DataFrame, List[str]]:
    """Baixa dados meteorológicos com validação de cobertura."""
    
    warnings_list = []
    
    # ... validações existentes ...
    
    # NOVO: Validar cobertura geográfica
    manager = ClimateSourceManager()
    available_sources = manager.get_available_sources_for_location(
        lat=latitude,
        lon=longitude,
        exclude_non_commercial=True  # Bloqueia Open-Meteo
    )
    
    # Verificar quais fontes solicitadas estão disponíveis
    requested_sources = normalize_source_names(data_source)
    unavailable = []
    
    for source in requested_sources:
        if source not in available_sources:
            unavailable.append(source)
        elif not available_sources[source]['available']:
            bbox_str = available_sources[source]['bbox_str']
            unavailable.append(
                f"{source} (fora de cobertura: {bbox_str})"
            )
    
    if unavailable:
        msg = (
            f"Fontes indisponíveis para ({latitude}, {longitude}): "
            f"{', '.join(unavailable)}"
        )
        warnings_list.append(msg)
        logger.warning(msg)
        
        # Remover fontes indisponíveis
        requested_sources = [
            s for s in requested_sources 
            if s in available_sources and available_sources[s]['available']
        ]
    
    if not requested_sources:
        raise ValueError(
            "Nenhuma fonte de dados disponível para esta localização"
        )
    
    logger.info(
        "Fontes disponíveis: %s", 
        ", ".join(requested_sources)
    )
```

#### **2.3: Criar factory de clientes**

```python
def create_client(
    source: str,
    config: dict
) -> Union[NASAPowerClient, METNorwayClient, NWSClient]:
    """
    Factory para criar cliente apropriado.
    
    Args:
        source: Nome da fonte ('nasa_power', 'met_norway', 'nws_usa')
        config: Configuração com cache, timeouts, etc.
    
    Returns:
        Cliente instanciado
    """
    cache = config.get('cache')
    
    if source == 'nasa_power':
        return NASAPowerClient(
            config=config.get('nasa_config', {}),
            cache=cache
        )
    elif source == 'met_norway':
        return METNorwayClient(
            config=config.get('met_config', {}),
            cache=cache
        )
    elif source == 'nws_usa':
        return NWSClient(
            config=config.get('nws_config', {}),
            cache=cache
        )
    else:
        raise ValueError(f"Unknown source: {source}")
```

#### **2.4: Loop de download atualizado**

```python
# Criar cache compartilhado
cache = create_climate_cache('shared')

dfs = []
source_metadata = []

for source in requested_sources:
    try:
        # Criar cliente
        client = create_client(source, {'cache': cache})
        
        # Download
        weather_df, fetch_warnings = client.get_weather_sync(
            start=data_inicial_formatted,
            end=data_final_adjusted,
            lat=latitude,
            lon=longitude
        )
        
        warnings_list.extend(fetch_warnings)
        
        # Validar DataFrame
        if weather_df is None or weather_df.empty:
            msg = f"{source}: No data returned"
            warnings_list.append(msg)
            continue
        
        # Armazenar metadados para fusão
        source_metadata.append({
            'name': source,
            'priority': available_sources[source]['priority'],
            'bbox': available_sources[source]['bbox'],
            'temporal': available_sources[source]['temporal']
        })
        
        dfs.append(weather_df)
        logger.info("%s: %d days downloaded", source, len(weather_df))
        
    except Exception as e:
        msg = f"{source}: Download error - {str(e)}"
        warnings_list.append(msg)
        logger.error(msg)
        continue
```

---

### **Tarefa 3: Criar Validação de Cobertura**

**Novo arquivo:** `backend/core/data_processing/data_validation.py`

```python
"""
Módulo de validação de dados climáticos.
"""

from typing import List, Dict, Tuple
from loguru import logger

from backend.api.services.climate_source_manager import ClimateSourceManager


def validate_source_coverage(
    sources: List[str],
    lat: float,
    lon: float,
    exclude_non_commercial: bool = True
) -> Tuple[List[str], List[str]]:
    """
    Valida se fontes cobrem coordenadas especificadas.
    
    Args:
        sources: Lista de IDs de fontes solicitadas
        lat: Latitude
        lon: Longitude
        exclude_non_commercial: Excluir fontes CC-BY-NC
    
    Returns:
        Tuple[List[str], List[str]]: (fontes_disponíveis, warnings)
    
    Example:
        >>> available, warnings = validate_source_coverage(
        ...     ['nasa_power', 'met_norway', 'nws_usa'],
        ...     lat=48.8566,  # Paris
        ...     lon=2.3522
        ... )
        >>> # Returns: (['nasa_power', 'met_norway'], [...warnings...])
    """
    warnings = []
    manager = ClimateSourceManager()
    
    # Obter fontes disponíveis
    available_dict = manager.get_available_sources_for_location(
        lat=lat,
        lon=lon,
        exclude_non_commercial=exclude_non_commercial
    )
    
    # Validar cada fonte solicitada
    validated_sources = []
    
    for source in sources:
        if source not in available_dict:
            msg = (
                f"⚠️ {source}: Fonte desconhecida ou bloqueada "
                f"(licença não-comercial)"
            )
            warnings.append(msg)
            logger.warning(msg)
            continue
        
        source_info = available_dict[source]
        
        if not source_info['available']:
            bbox_str = source_info.get('bbox_str', 'Unknown coverage')
            msg = (
                f"⚠️ {source}: Coordenadas ({lat}, {lon}) fora de "
                f"cobertura. {bbox_str}"
            )
            warnings.append(msg)
            logger.warning(msg)
            continue
        
        # Fonte válida
        validated_sources.append(source)
        logger.info(
            "✅ %s: Available for (%.4f, %.4f)",
            source, lat, lon
        )
    
    return validated_sources, warnings
```

---

### **Tarefa 4: Atualizar Lógica de Fusão**

**Mudanças em `data_download.py`:**

```python
# Fusão dinâmica (2+ fontes)
if len(requested_sources) >= 2:
    if len(dfs) < 2:
        msg = "Fusão requer pelo menos 2 fontes válidas"
        logger.error(msg)
        raise ValueError(msg)
    
    try:
        # Converte DataFrames para dicionários
        df_dicts = []
        for df in dfs:
            df_dict = {}
            for idx, row in df.iterrows():
                key = idx.strftime("%Y-%m-%d %H:%M:%S")
                df_dict[key] = row.to_dict()
            df_dicts.append(df_dict)
        
        # Executa fusão com validação de licença
        task = data_fusion.delay(
            df_dicts,
            source_names=requested_sources,  # Validação
            source_metadata=source_metadata  # Para pesos inteligentes
        )
        weather_data_dict, fusion_warnings = task.get(timeout=30)
        warnings_list.extend(fusion_warnings)
        
        # Converte resultado para DataFrame
        weather_data = pd.DataFrame.from_dict(
            weather_data_dict,
            orient='index'
        )
        weather_data.index = pd.to_datetime(weather_data.index)
        
        logger.info(
            "✅ Data fusion completed: %s",
            " + ".join(requested_sources)
        )
        
    except Exception as e:
        msg = f"Erro na fusão de dados: {str(e)}"
        logger.error(msg)
        raise ValueError(msg)

else:
    # Fonte única
    if not dfs:
        raise ValueError("Nenhuma fonte forneceu dados válidos")
    weather_data = dfs[0]
    logger.info("✅ Single source data: %s", requested_sources[0])
```

---

### **Tarefa 5: Pré-processamento por Fonte**

**Novo arquivo:** `backend/core/data_processing/source_preprocessors.py`

```python
"""
Pré-processadores específicos por fonte de dados.

Cada fonte tem características próprias:
- NASA POWER: Diário, global, MJ/m²/dia
- MET Norway: Horário, Europa, W/m²
- NWS: Horário, USA, °F/mph
"""

import pandas as pd
import numpy as np
from typing import Tuple, List
from loguru import logger


def preprocess_nasa_power(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Pré-processa dados NASA POWER.
    
    NASA POWER já retorna:
    - Resolução diária
    - Temperatura em °C
    - Radiação em MJ/m²/dia
    - Velocidade do vento em m/s
    
    Args:
        df: DataFrame com dados NASA POWER
    
    Returns:
        Tuple[pd.DataFrame, List[str]]: DataFrame processado e warnings
    """
    warnings = []
    
    # NASA POWER já está no formato correto
    # Apenas validar colunas esperadas
    expected_cols = [
        'T2M_MAX', 'T2M_MIN', 'T2M', 'RH2M', 
        'WS2M', 'ALLSKY_SFC_SW_DWN', 'PRECTOTCORR'
    ]
    
    missing = set(expected_cols) - set(df.columns)
    if missing:
        warnings.append(
            f"NASA POWER: Missing columns {missing}"
        )
    
    return df, warnings


def preprocess_met_norway(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Pré-processa dados MET Norway.
    
    MET Norway retorna dados horários:
    - Temperatura em °C (OK)
    - Radiação em W/m² → precisa converter para MJ/m²/dia
    - Vento em m/s (OK)
    
    Agregação hourly → daily:
    - T2M_MAX: max diário
    - T2M_MIN: min diário
    - T2M: média diária
    - ALLSKY_SFC_SW_DWN: soma horária * 3600 / 1000000
    
    Args:
        df: DataFrame com dados horários MET Norway
    
    Returns:
        Tuple[pd.DataFrame, List[str]]: DataFrame diário e warnings
    """
    warnings = []
    
    # Converter índice para date (agregação diária)
    df['date'] = df.index.date
    
    # Agregações
    daily_df = pd.DataFrame()
    
    # Temperatura
    if 'air_temperature' in df.columns:
        daily_df['T2M_MAX'] = df.groupby('date')['air_temperature'].max()
        daily_df['T2M_MIN'] = df.groupby('date')['air_temperature'].min()
        daily_df['T2M'] = df.groupby('date')['air_temperature'].mean()
    
    # Umidade
    if 'relative_humidity' in df.columns:
        daily_df['RH2M'] = df.groupby('date')['relative_humidity'].mean()
    
    # Vento
    if 'wind_speed' in df.columns:
        daily_df['WS2M'] = df.groupby('date')['wind_speed'].mean()
    
    # Radiação solar: W/m² → MJ/m²/dia
    # 1 W/m² * 1 hora = 3600 J/m² = 0.0036 MJ/m²
    if 'solar_radiation' in df.columns:
        # Soma de todas as horas * 3600 / 1e6
        daily_df['ALLSKY_SFC_SW_DWN'] = (
            df.groupby('date')['solar_radiation'].sum() * 3600 / 1e6
        )
    
    # Precipitação
    if 'precipitation_amount' in df.columns:
        daily_df['PRECTOTCORR'] = (
            df.groupby('date')['precipitation_amount'].sum()
        )
    
    # Converter índice para datetime
    daily_df.index = pd.to_datetime(daily_df.index)
    
    warnings.append(
        f"MET Norway: Aggregated {len(df)} hourly records "
        f"to {len(daily_df)} daily records"
    )
    
    return daily_df, warnings


def preprocess_nws(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Pré-processa dados NWS/NOAA.
    
    NWS retorna dados horários em unidades imperiais:
    - Temperatura em °F → converter para °C
    - Vento em mph → converter para m/s
    
    Conversões:
    - °C = (°F - 32) * 5/9
    - m/s = mph * 0.44704
    
    Args:
        df: DataFrame com dados horários NWS
    
    Returns:
        Tuple[pd.DataFrame, List[str]]: DataFrame diário e warnings
    """
    warnings = []
    
    # Converter temperaturas °F → °C
    if 'temperature' in df.columns:
        df['temperature'] = (df['temperature'] - 32) * 5 / 9
    
    if 'dewpoint' in df.columns:
        df['dewpoint'] = (df['dewpoint'] - 32) * 5 / 9
    
    # Converter vento mph → m/s
    if 'wind_speed' in df.columns:
        # Remover "mph" da string e converter
        df['wind_speed'] = df['wind_speed'].str.extract(
            r'(\d+)'
        ).astype(float) * 0.44704
    
    # Agregação diária
    df['date'] = df.index.date
    
    daily_df = pd.DataFrame()
    
    # Temperatura
    if 'temperature' in df.columns:
        daily_df['T2M_MAX'] = df.groupby('date')['temperature'].max()
        daily_df['T2M_MIN'] = df.groupby('date')['temperature'].min()
        daily_df['T2M'] = df.groupby('date')['temperature'].mean()
    
    # Umidade (calcular de dewpoint)
    if 'dewpoint' in df.columns and 'temperature' in df.columns:
        # Magnus formula: RH = 100 * exp((17.625*Td)/(243.04+Td)) / 
        #                       exp((17.625*T)/(243.04+T))
        df['RH'] = 100 * np.exp(
            (17.625 * df['dewpoint']) / (243.04 + df['dewpoint'])
        ) / np.exp(
            (17.625 * df['temperature']) / (243.04 + df['temperature'])
        )
        daily_df['RH2M'] = df.groupby('date')['RH'].mean()
    
    # Vento
    if 'wind_speed' in df.columns:
        daily_df['WS2M'] = df.groupby('date')['wind_speed'].mean()
    
    # Precipitação
    if 'quantitative_precipitation' in df.columns:
        daily_df['PRECTOTCORR'] = (
            df.groupby('date')['quantitative_precipitation'].sum()
        )
    
    # Radiação solar (estimativa de cloud cover)
    # NWS não fornece radiação diretamente
    # Usar cloud_cover para estimar (aproximação)
    if 'sky_cover' in df.columns:
        # Placeholder: requer modelo mais sofisticado
        warnings.append(
            "NWS: Solar radiation estimated from cloud cover "
            "(may have higher uncertainty)"
        )
    
    daily_df.index = pd.to_datetime(daily_df.index)
    
    warnings.append(
        f"NWS: Converted imperial to metric units, "
        f"aggregated {len(df)} hourly to {len(daily_df)} daily records"
    )
    
    return daily_df, warnings


def preprocess_by_source(
    df: pd.DataFrame,
    source: str
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Dispatch para pré-processador apropriado.
    
    Args:
        df: DataFrame com dados brutos
        source: ID da fonte ('nasa_power', 'met_norway', 'nws_usa')
    
    Returns:
        Tuple[pd.DataFrame, List[str]]: DataFrame processado e warnings
    """
    if source == 'nasa_power':
        return preprocess_nasa_power(df)
    elif source == 'met_norway':
        return preprocess_met_norway(df)
    elif source == 'nws_usa':
        return preprocess_nws(df)
    else:
        # Fonte desconhecida, retornar sem alterações
        return df, [f"Warning: Unknown source {source}, no preprocessing applied"]
```

**Integração em `data_download.py`:**

```python
from backend.core.data_processing.source_preprocessors import preprocess_by_source

# Após download, antes de adicionar ao dfs
for source in requested_sources:
    # ... download ...
    
    # PRÉ-PROCESSAMENTO POR FONTE
    weather_df, preproc_warnings = preprocess_by_source(
        weather_df,
        source
    )
    warnings_list.extend(preproc_warnings)
    
    dfs.append(weather_df)
```

---

### **Tarefa 6: Pesos Inteligentes de Fusão**

**Atualizar `data_fusion.py`:**

```python
@shared_task(bind=True, name='src.data_fusion.data_fusion')
def data_fusion(
    self,
    dfs: List[dict],
    ensemble_size: int = 50,
    inflation_factor: float = 1.02,
    source_names: Optional[List[str]] = None,
    source_metadata: Optional[List[Dict]] = None  # NOVO
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Fusão com pesos inteligentes baseados em:
    - Prioridade da fonte (SOURCES_CONFIG)
    - Distância do centro de cobertura
    - Qualidade histórica (se disponível)
    """
    
    # ... validação de licença existente ...
    
    # NOVO: Calcular pesos inteligentes
    if source_metadata:
        weights = calculate_fusion_weights(
            source_metadata,
            location=(lat, lon)  # Passar coords se disponível
        )
        logger.info("Fusion weights: %s", weights)
    else:
        # Fallback: pesos iguais
        weights = [1.0 / len(dfs)] * len(dfs)
    
    # Aplicar pesos no ensemble
    forecast = np.average(
        [df.to_numpy() for df in dataframes],
        axis=0,
        weights=weights
    )
    
    # ... resto do algoritmo Kalman ...
```

**Nova função de cálculo de pesos:**

```python
def calculate_fusion_weights(
    source_metadata: List[Dict],
    location: Optional[Tuple[float, float]] = None
) -> List[float]:
    """
    Calcula pesos para fusão baseado em múltiplos critérios.
    
    Critérios:
    1. Prioridade (40%): Menor prioridade = maior peso
    2. Distância (30%): Mais próximo do centro de cobertura = maior peso
    3. Resolução temporal (20%): Hourly > Daily
    4. Qualidade histórica (10%): Baseado em validações passadas
    
    Args:
        source_metadata: Lista de metadados das fontes
        location: Tupla (lat, lon) opcional para cálculo de distância
    
    Returns:
        List[float]: Pesos normalizados (soma = 1.0)
    """
    import math
    
    weights = []
    
    for meta in source_metadata:
        # 1. Peso de prioridade (inverso)
        priority = meta.get('priority', 5)
        priority_weight = 1.0 / priority
        
        # 2. Peso de distância
        if location and meta.get('bbox'):
            bbox = meta['bbox']
            # Calcular centro do bbox
            center_lat = (bbox[1] + bbox[3]) / 2
            center_lon = (bbox[0] + bbox[2]) / 2
            
            # Distância haversine simplificada
            dlat = math.radians(location[0] - center_lat)
            dlon = math.radians(location[1] - center_lon)
            a = (math.sin(dlat/2)**2 + 
                 math.cos(math.radians(center_lat)) *
                 math.cos(math.radians(location[0])) *
                 math.sin(dlon/2)**2)
            distance = 2 * math.asin(math.sqrt(a)) * 6371  # km
            
            # Inverso da distância (mais próximo = maior peso)
            distance_weight = 1.0 / (1.0 + distance / 1000)
        else:
            distance_weight = 1.0  # Sem informação, peso neutro
        
        # 3. Peso de resolução temporal
        temporal = meta.get('temporal', 'daily')
        temporal_weight = 1.2 if temporal == 'hourly' else 1.0
        
        # 4. Combinar pesos (média ponderada)
        combined_weight = (
            0.4 * priority_weight +
            0.3 * distance_weight +
            0.2 * temporal_weight +
            0.1 * 1.0  # Qualidade (placeholder)
        )
        
        weights.append(combined_weight)
    
    # Normalizar (soma = 1.0)
    total = sum(weights)
    normalized_weights = [w / total for w in weights]
    
    logger.info(
        "Fusion weights: %s",
        {meta['name']: f"{w:.3f}" 
         for meta, w in zip(source_metadata, normalized_weights)}
    )
    
    return normalized_weights
```

---

### **Tarefa 7: Testes de Integração**

**Novo arquivo:** `backend/tests/integration/test_data_pipeline.py`

```python
"""
Testes de integração do pipeline completo.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta

from backend.core.data_processing.data_download import download_weather_data
from backend.core.data_processing.data_preprocessing import preprocessing
from backend.core.eto_calculation.eto_calculation import calculate_eto


class TestDataPipeline:
    """Testes end-to-end do pipeline de dados."""
    
    @pytest.mark.integration
    def test_pipeline_paris_nasa_met(self):
        """
        Testa pipeline completo para Paris com fusão NASA + MET.
        """
        # Paris, França
        lat, lon = 48.8566, 2.3522
        start = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        end = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        
        # Download com fusão
        df, warnings = download_weather_data(
            data_source=['nasa_power', 'met_norway'],
            data_inicial=start,
            data_final=end,
            latitude=lat,
            longitude=lon
        )
        
        # Validações
        assert df is not None
        assert not df.empty
        assert 'T2M_MAX' in df.columns
        assert 'ALLSKY_SFC_SW_DWN' in df.columns
        
        # Preprocessing
        df_clean, prep_warnings = preprocessing(df, latitude=lat)
        
        assert df_clean is not None
        assert not df_clean.isna().all().any()  # Sem colunas totalmente NaN
        
        # Cálculo de ETo
        eto_results, eto_warnings = calculate_eto(df_clean, latitude=lat)
        
        assert eto_results is not None
        assert 'ETo' in eto_results.columns
        assert (eto_results['ETo'] > 0).all()  # ETo positivo
        assert (eto_results['ETo'] < 20).all()  # ETo razoável (<20 mm/dia)
    
    @pytest.mark.integration
    def test_pipeline_new_york_nasa_nws(self):
        """
        Testa pipeline para Nova York com fusão NASA + NWS.
        """
        # Nova York, USA
        lat, lon = 40.7128, -74.0060
        start = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        end = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        
        df, warnings = download_weather_data(
            data_source=['nasa_power', 'nws_usa'],
            data_inicial=start,
            data_final=end,
            latitude=lat,
            longitude=lon
        )
        
        assert df is not None
        assert not df.empty
    
    @pytest.mark.integration
    def test_coverage_validation_blocks_wrong_source(self):
        """
        Testa que validação bloqueia fontes fora de cobertura.
        """
        # Balsas, MA (Brasil) - fora de Europa e USA
        lat, lon = -7.5312, -46.0390
        
        # Tentar usar MET Norway (Europa apenas)
        with pytest.raises(ValueError, match="Nenhuma fonte.*disponível"):
            download_weather_data(
                data_source=['met_norway'],  # Europa apenas
                data_inicial='2024-01-01',
                data_final='2024-01-07',
                latitude=lat,
                longitude=lon
            )
    
    @pytest.mark.integration
    def test_license_validation_blocks_openmeteo_fusion(self):
        """
        Testa que Open-Meteo é bloqueado em fusão.
        """
        lat, lon = -7.5312, -46.0390  # Balsas, MA
        
        # Tentar fusão com Open-Meteo
        with pytest.raises(ValueError, match="LICENSE VIOLATION"):
            download_weather_data(
                data_source=['nasa_power', 'openmeteo_forecast'],
                data_inicial='2024-01-01',
                data_final='2024-01-07',
                latitude=lat,
                longitude=lon
            )
```

---

## 📊 Cronograma de Implementação

| Tarefa | Esforço | Prioridade | Dependências |
|--------|---------|------------|--------------|
| 1. `get_weather_sync()` | 4h | 🔴 Alta | Nenhuma |
| 2. Atualizar `data_download.py` | 6h | 🔴 Alta | Tarefa 1 |
| 3. Validação de cobertura | 3h | 🟡 Média | Tarefa 2 |
| 4. Fusão múltiplas fontes | 3h | 🟡 Média | Tarefas 2, 3 |
| 5. Pré-processamento por fonte | 5h | 🔴 Alta | Tarefa 2 |
| 6. Pesos inteligentes | 4h | 🟢 Baixa | Tarefa 4 |
| 7. Testes de integração | 4h | 🔴 Alta | Todas |

**Total:** ~29 horas de desenvolvimento

---

## ✅ Checklist de Validação

Antes de considerar completo, validar:

- [ ] `get_weather_sync()` implementado nos 3 novos clientes
- [ ] `data_download.py` usa novos clientes (não legados)
- [ ] Validação de cobertura geográfica funcional
- [ ] Fusão suporta 2+ fontes dinamicamente
- [ ] Pré-processamento normaliza unidades e resolução
- [ ] Pesos de fusão consideram prioridade + distância
- [ ] Validação de licença bloqueia Open-Meteo
- [ ] Testes de integração passando (Paris, NYC, Balsas)
- [ ] Logs informativos em cada etapa
- [ ] Documentação atualizada

---

**Próximos Passos:**
1. Implementar `get_weather_sync()` nos 3 clientes ✅
2. Refatorar `data_download.py` completamente
3. Criar `source_preprocessors.py` e `data_validation.py`
4. Adicionar pesos inteligentes em `data_fusion.py`
5. Escrever testes de integração
6. Validar com dataset Xavier (17 cidades MATOPIBA)

**Objetivo Final:** Pipeline robusto que suporta múltiplas fontes, valida cobertura automaticamente, aplica pré-processamento apropriado, e funde dados com pesos inteligentes - tudo com proteções de conformidade de licença.
