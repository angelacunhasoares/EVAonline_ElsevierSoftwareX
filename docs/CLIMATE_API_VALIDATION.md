# 🔍 Validação das APIs Climáticas contra Documentação Oficial

**Data**: 14 de Outubro de 2025  
**Objetivo**: Verificar conformidade dos clientes com APIs oficiais

---

## 📚 Documentações Oficiais Consultadas

1. **NASA POWER**: https://power.larc.nasa.gov/api/pages/?urls.primaryName=Daily
2. **MET Norway (Frost API)**: https://frost.met.no/api.html
3. **NWS (NOAA)**: https://api.weather.gov/openapi.json

---

## 🔴 DESCOBERTA CRÍTICA: MET Norway API

### ⚠️ PROBLEMA: Estamos usando API ERRADA

**Nossa implementação atual**:
```python
# met_norway_client.py (LINHA 32)
base_url: str = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
```

**PROBLEMA IDENTIFICADO**:
- ✅ **Forecast API** (https://api.met.no/weatherapi/locationforecast/2.0/) - Dados de PREVISÃO (0-10 dias futuro)
- ❌ **Frost API** (https://frost.met.no/observations/v0.jsonld) - Dados HISTÓRICOS

**O que precisamos**:
- Para **ETo cálculo**: Precisamos dados HISTÓRICOS + Atuais
- **Solução**: Usar **Frost API** (requer autenticação)

### 🔧 Frost API vs LocationForecast API

| Característica | LocationForecast API | Frost API |
|----------------|---------------------|-----------|
| **URL** | api.met.no/weatherapi/locationforecast | frost.met.no/observations |
| **Propósito** | Previsão meteorológica (futuro) | Dados observados (histórico) |
| **Autenticação** | Não requer | **Client ID obrigatório** |
| **Cobertura** | Qualquer ponto da Europa | Estações meteorológicas |
| **Dados** | Previsão 0-10 dias | Histórico desde 1800s |
| **Rate Limit** | ~20 req/s | ~20 req/s |
| **Para ETo** | ❌ Previsão não serve | ✅ Ideal |

### 📝 Frost API - Como Usar

**1. Registrar Client ID**:
```
https://frost.met.no/auth/requestCredentials.html
```

**2. Endpoint Correto**:
```
https://frost.met.no/observations/v0.jsonld
```

**3. Headers Obrigatórios**:
```python
headers = {
    'Authorization': f'{client_id}',  # Client ID da Frost API
    'User-Agent': 'EVAonline/1.0 (contact@example.com)'
}
```

**4. Parâmetros**:
```python
params = {
    'sources': 'SN18700',  # Station ID
    'referencetime': '2024-10-01/2024-10-07',
    'elements': 'air_temperature,relative_humidity,wind_speed,sum(precipitation_amount PT1H)',
    'timeoffsets': 'PT0H',  # Horário exato
    'levels': 'default'
}
```

**5. Response Example**:
```json
{
  "@context": "https://frost.met.no/schema",
  "@type": "ObservationResponse",
  "apiVersion": "v0",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "data": [
    {
      "sourceId": "SN18700:0",
      "referenceTime": "2024-10-01T00:00:00.000Z",
      "observations": [
        {
          "elementId": "air_temperature",
          "value": 15.2,
          "unit": "degC"
        }
      ]
    }
  ]
}
```

---

## ✅ NASA POWER - Status OK

### Validação da Documentação

**Base URL**: ✅ CORRETO
```python
base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
```

**Parâmetros**: ✅ CORRETOS
```python
params = {
    "parameters": "T2M_MAX,T2M_MIN,T2M,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR",
    "community": "AG",  # Agriculture
    "longitude": lon,
    "latitude": lat,
    "start": "20241001",  # YYYYMMDD
    "end": "20241007",    # YYYYMMDD
    "format": "JSON"
}
```

**Rate Limits**: ⚠️ DOCUMENTAR
- Não há rate limit oficial documentado
- Recomendado: ~10 req/s (conservador)
- **Adicionar throttling se necessário**

**Delay dos Dados**: ✅ DOCUMENTADO CORRETAMENTE
```python
# nasa_power_client.py linha 77
"delay_hours": 72,  # 2-3 dias de atraso
```

### 🔧 Melhorias Sugeridas

**1. Adicionar validação de response**:
```python
def _parse_response(self, data: Dict) -> List[NASAPowerData]:
    """Parse NASA POWER response com validação."""
    
    # Validação robusta
    if "properties" not in data:
        raise ValueError("Resposta sem 'properties'")
    
    props = data["properties"]
    
    if "parameter" not in props:
        raise ValueError("Resposta sem 'parameter'")
    
    parameters = props["parameter"]
    
    # Validar que temos as variáveis esperadas
    required_params = ["T2M_MAX", "T2M_MIN", "T2M", "RH2M"]
    missing = [p for p in required_params if p not in parameters]
    
    if missing:
        logger.warning(f"NASA POWER: Faltando parâmetros {missing}")
    
    # Continuar parseando...
```

**2. Adicionar retry com backoff exponencial**:
```python
import asyncio
from datetime import timedelta

async def _fetch_with_retry(self, url: str, params: dict, max_retries: int = 3):
    """Fetch com retry e backoff exponencial."""
    
    for attempt in range(max_retries):
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limit
                # Backoff exponencial: 1s, 2s, 4s
                wait_time = 2 ** attempt
                logger.warning(
                    f"NASA POWER rate limit (429). "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                raise
        
        except httpx.RequestError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)
    
    raise Exception("Max retries exceeded")
```

---

## ✅ NWS (NOAA) - Status OK

### Validação da Documentação

**API Flow**: ✅ CORRETO (2-step)
```python
# Step 1: Get metadata
GET /points/{lat},{lon}
→ Returns: gridId, gridX, gridY, forecastHourly URL

# Step 2: Get forecast
GET /gridpoints/{office}/{gridX},{gridY}/forecast/hourly
→ Returns: hourly forecast data
```

**Headers**: ✅ CORRETOS
```python
headers = {
    "User-Agent": "EVAonline/1.0 (https://github.com/angelacunhasoares/EVAonline)",
    "Accept": "application/geo+json"  # Ou application/ld+json
}
```

**OpenAPI Spec**: ✅ VALIDADO
- Nossa implementação está 100% conforme com spec OpenAPI 3.0.3
- Endpoints corretos
- Schemas corretos

### 🔧 Melhorias Sugeridas

**1. Adicionar suporte a observações atuais** (além de forecast):
```python
async def get_current_observations(
    self,
    lat: float,
    lon: float
) -> List[NWSData]:
    """
    Busca observações ATUAIS (não previsão).
    
    Útil para dados em tempo real combinados com forecast.
    """
    # Step 1: Get metadata
    grid_metadata = await self._get_grid_metadata(lat, lon)
    
    # Step 2: Get observation stations
    stations_url = grid_metadata.get("observationStations")
    response = await self.client.get(stations_url)
    stations_data = response.json()
    
    # Step 3: Get latest observation from first station
    if stations_data["features"]:
        station_url = stations_data["features"][0]["id"]
        obs_url = f"{station_url}/observations/latest"
        
        response = await self.client.get(obs_url)
        obs_data = response.json()
        
        return self._parse_observation(obs_data)
    
    return []
```

**2. Adicionar conversão de unidades** (NWS retorna imperial):
```python
def _fahrenheit_to_celsius(self, temp_f: float) -> float:
    """Converte Fahrenheit → Celsius."""
    return (temp_f - 32) * 5/9

def _mph_to_ms(self, wind_mph: float) -> float:
    """Converte mph → m/s."""
    return wind_mph * 0.44704

def _parse_forecast_response(self, data: Dict, ...) -> List[NWSData]:
    """Parse com conversões de unidade."""
    
    for period in periods:
        temp_f = period.get("temperature")
        temp_c = self._fahrenheit_to_celsius(temp_f) if temp_f else None
        
        # Vento pode vir como string "5 mph" ou número
        wind_str = period.get("windSpeed", "")
        wind_mph = self._extract_wind_speed(wind_str)
        wind_ms = self._mph_to_ms(wind_mph) if wind_mph else None
        
        record = NWSData(
            timestamp=period["startTime"],
            temp_celsius=temp_c,
            wind_speed_ms=wind_ms,
            ...
        )
```

---

## 🚨 Ações Corretivas Necessárias

### Prioridade ALTA

**1. MET Norway - Implementar Frost API** ⚠️
```python
# backend/api/services/met_norway_frost_client.py (NOVO)
class METNorwayFrostClient:
    """Cliente para Frost API (dados observados)."""
    
    def __init__(self, client_id: str, cache: Optional[any] = None):
        self.client_id = client_id
        self.base_url = "https://frost.met.no/observations/v0.jsonld"
        self.cache = cache
        
        headers = {
            'Authorization': client_id,
            'User-Agent': 'EVAonline/1.0 (contact@example.com)'
        }
        
        self.client = httpx.AsyncClient(
            timeout=30,
            headers=headers
        )
    
    async def get_observations(
        self,
        station_id: str,
        start: datetime,
        end: datetime,
        elements: List[str]
    ) -> List[METNorwayObservation]:
        """Busca observações históricas."""
        
        params = {
            'sources': station_id,
            'referencetime': f"{start.isoformat()}/{end.isoformat()}",
            'elements': ','.join(elements),
            'timeoffsets': 'PT0H'
        }
        
        response = await self.client.get(self.base_url, params=params)
        response.raise_for_status()
        
        return self._parse_observations(response.json())
```

**2. Registrar Frost API Client ID**:
- Acessar: https://frost.met.no/auth/requestCredentials.html
- Registrar aplicação
- Adicionar Client ID às variáveis de ambiente:
  ```bash
  MET_NORWAY_FROST_CLIENT_ID=your_client_id_here
  ```

**3. Encontrar estações próximas**:
```python
async def find_nearest_station(self, lat: float, lon: float) -> str:
    """Encontra estação MET Norway mais próxima."""
    
    url = "https://frost.met.no/sources/v0.jsonld"
    params = {
        'types': 'SensorSystem',
        'geometry': f'POINT({lon} {lat})',
        'nearestmaxcount': 1
    }
    
    response = await self.client.get(url, params=params)
    data = response.json()
    
    if data["data"]:
        return data["data"][0]["id"]
    
    raise ValueError(f"Nenhuma estação encontrada perto de ({lat}, {lon})")
```

### Prioridade MÉDIA

**4. NASA POWER - Adicionar retry com backoff**:
```python
# Implementar _fetch_with_retry() no nasa_power_client.py
```

**5. NWS - Adicionar suporte a observações atuais**:
```python
# Implementar get_current_observations() no nws_client.py
```

**6. Todos os clientes - Adicionar métricas Prometheus**:
```python
from prometheus_client import Counter, Histogram

CLIMATE_API_REQUESTS = Counter(
    'climate_api_requests_total',
    'Total API requests',
    ['source', 'status']
)

CLIMATE_API_DURATION = Histogram(
    'climate_api_duration_seconds',
    'API request duration',
    ['source']
)

# No código
with CLIMATE_API_DURATION.labels(source="nasa_power").time():
    response = await self.client.get(...)
    CLIMATE_API_REQUESTS.labels(source="nasa_power", status="success").inc()
```

---

## 📊 Comparação: Dados Históricos vs Forecast

| Fonte | Dados Históricos | Dados Forecast | Para ETo |
|-------|-----------------|----------------|----------|
| **NASA POWER** | ✅ Desde 1981 (delay 2-7 dias) | ❌ Não tem | ✅ Perfeito |
| **MET Norway Forecast** | ❌ Não tem | ✅ 0-10 dias futuro | ❌ Não serve |
| **MET Norway Frost** | ✅ Desde 1800s | ❌ Não tem | ✅ Perfeito |
| **NWS Forecast** | ❌ Não tem | ✅ 0-7 dias futuro | ❌ Não serve |
| **NWS Observations** | ✅ Últimas 24h | ❌ Não tem | ✅ Complementar |

### 💡 Estratégia Recomendada para ETo

**Para dados HISTÓRICOS/ATUAIS** (cálculo de ETo):
1. **Global**: NASA POWER (delay 2-7 dias, mas cobertura global)
2. **Europa**: MET Norway Frost API (estações, tempo real)
3. **USA**: NWS Observations (tempo real) + NASA POWER (histórico)

**Para dados FORECAST** (previsão futura):
- Não usar para ETo (ETo é baseado em dados observados)
- Manter APIs de forecast para outros propósitos do sistema

---

## ✅ Checklist de Validação

### NASA POWER
- [x] Base URL correto
- [x] Parâmetros corretos
- [x] Headers corretos
- [x] Delay documentado
- [ ] Rate limiting implementado
- [ ] Retry com backoff

### MET Norway
- [ ] ⚠️ **TROCAR PARA FROST API**
- [ ] Registrar Client ID
- [ ] Implementar autenticação
- [ ] Implementar busca de estações
- [ ] Testar integração

### NWS (NOAA)
- [x] API flow (2-step) correto
- [x] Headers corretos
- [x] Schemas validados
- [ ] Conversões de unidade (F→C, mph→m/s)
- [ ] Suporte a observações atuais
- [ ] Retry com backoff

---

## 🎯 Próximos Passos

1. **URGENTE**: Implementar MET Norway Frost API
2. **ALTA**: Registrar Client ID na Frost API
3. **ALTA**: Adicionar retry com backoff (todos os clientes)
4. **MÉDIA**: Adicionar métricas Prometheus
5. **MÉDIA**: NWS - conversões de unidade e observações
6. **BAIXA**: Testes de integração com APIs reais

---

**Gerado em**: 2025-10-14  
**Próxima revisão**: Após implementação Frost API
