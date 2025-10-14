# 🌍 Auditoria Completa: Clientes de API Climática

**Data**: 13 de Outubro de 2025  
**Objetivo**: Revisar implementação, integração e documentação dos clientes NASA POWER, MET Norway e NWS

---

## 📋 Executive Summary

### Status Geral

| Cliente | Status | Redis | Cache Service | Async | Celery | PostgreSQL | Documentação |
|---------|--------|-------|---------------|-------|--------|------------|--------------|
| **nasa_power_client.py** | ✅ BOM | ⚠️ INJETADO | ✅ SIM | ✅ ASYNC | ❌ NÃO | ❌ NÃO | ✅ EXCELENTE |
| **met_norway_client.py** | ✅ BOM | ⚠️ INJETADO | ✅ SIM | ✅ ASYNC | ❌ NÃO | ❌ NÃO | ✅ EXCELENTE |
| **nws_client.py** | ✅ BOM | ⚠️ INJETADO | ✅ SIM | ✅ ASYNC | ❌ NÃO | ❌ NÃO | ✅ EXCELENTE |
| **nasapower.py (LEGACY)** | ⚠️ DUPLICADO | ✅ DIRETO | ❌ NÃO | ❌ SYNC | ✅ SIM | ❌ NÃO | ⚠️ PARCIAL |

### Descobertas Críticas

🔴 **PROBLEMA 1**: Existem **2 implementações diferentes** da NASA POWER:
- `nasa_power_client.py` (NOVO) - Moderna, async, bem documentada
- `nasapower.py` (LEGACY) - Antiga, sync, com integração Celery

🟡 **PROBLEMA 2**: Nenhum cliente integrado com **PostgreSQL** para persistência

🟡 **PROBLEMA 3**: Cache via **injeção de dependência** (design correto), mas falta verificar se `ClimateCacheService` está sendo injetado corretamente

🟢 **PONTO FORTE**: Todos os clientes novos seguem **design patterns** consistentes e têm **documentação excelente**

---

## 🔍 Análise Detalhada por Cliente

### 1️⃣ nasa_power_client.py (NOVO - RECOMENDADO)

**Arquivo**: `backend/api/services/nasa_power_client.py`

#### ✅ Pontos Fortes

```python
class NASAPowerClient:
    """Cliente moderno com cache inteligente."""
    
    def __init__(self, config=None, cache=None):
        self.cache = cache  # ClimateCacheService injetado
        
    async def get_daily_data(...) -> List[NASAPowerData]:
        # 1. Tenta cache Redis
        if self.cache:
            cached = await self.cache.get(...)
            if cached:
                return cached
        
        # 2. Busca API
        response = await self.client.get(...)
        parsed = self._parse_response(data)
        
        # 3. Salva cache
        if self.cache and parsed:
            await self.cache.set(...)
        
        return parsed
```

**Características**:
- ✅ **Async/await**: Performance otimizada
- ✅ **Pydantic models**: `NASAPowerData` validado
- ✅ **Retry logic**: 3 tentativas com delay
- ✅ **Cache strategy**: Fluxo GET → API → SET
- ✅ **Global coverage**: Qualquer ponto do mundo
- ✅ **Domínio Público**: Sem restrições de uso
- ✅ **Health check**: Método `health_check()`
- ✅ **Documentação**: Docstrings completas

**Variáveis Suportadas**:
```python
"T2M_MAX",              # Temp máxima (°C)
"T2M_MIN",              # Temp mínima (°C)
"T2M",                  # Temp média (°C)
"RH2M",                 # Umidade relativa (%)
"WS2M",                 # Velocidade vento (m/s)
"ALLSKY_SFC_SW_DWN",    # Radiação solar (kWh/m²/day)
"PRECTOTCORR"           # Precipitação (mm/dia)
```

**Conversões Automáticas**:
```python
# Radiação: kWh/m²/day → MJ/m²/day (FAO-56)
solar_mj = solar_kwh * 3.6
```

#### ⚠️ Pontos de Atenção

1. **Cache Injection**:
```python
# Como está
client = NASAPowerClient(cache=cache_service)

# ❓ Verificar: cache_service está sendo injetado?
```

2. **Delay nos dados**:
```python
# NASA POWER tem atraso de 2-7 dias
async def get_current_delay() -> timedelta:
    return timedelta(days=2)  # Delay típico

# ⚠️ NÃO é fonte real-time!
# Para dados de HOJE, usar outra fonte
```

3. **Rate Limits**:
```python
# NASA POWER: ~1000 req/dia
# ⚠️ Implementar throttling se necessário
```

---

### 2️⃣ met_norway_client.py (EUROPA)

**Arquivo**: `backend/api/services/met_norway_client.py`

#### ✅ Pontos Fortes

```python
class METNorwayClient:
    """Cliente para Europa com CC-BY 4.0."""
    
    # Bounding box Europa
    EUROPE_BBOX = (-25.0, 35.0, 45.0, 72.0)  # (W, S, E, N)
    
    def is_in_coverage(self, lat: float, lon: float) -> bool:
        """Valida se coordenadas estão na Europa."""
        lon_min, lat_min, lon_max, lat_max = self.EUROPE_BBOX
        return (lon_min <= lon <= lon_max) and (lat_min <= lat <= lat_max)
```

**Características**:
- ✅ **Coverage check**: Valida bbox ANTES de requisição
- ✅ **User-Agent obrigatório**: Configurado corretamente
- ✅ **Attribution**: Método `get_attribution()` para compliance
- ✅ **Dados horários**: Resolução superior
- ✅ **Real-time**: Delay de ~1 hora apenas
- ✅ **Licença clara**: CC-BY 4.0 bem documentada

**Coverage Europa**:
```
Longitude: -25°W (Islândia) a 45°E (Rússia Ocidental)
Latitude: 35°N (Mediterrâneo) a 72°N (Norte da Noruega)

Países: Noruega, Suécia, Finlândia, Dinamarca, Islândia,
        UK, Irlanda, França, Alemanha, Espanha, Itália,
        Polônia, Holanda, Bélgica
```

**Atribuição Obrigatória**:
```python
def get_attribution(self) -> str:
    return "Weather data from MET Norway (CC BY 4.0)"

# ⚠️ DEVE ser exibido em TODAS as visualizações!
```

#### ⚠️ Pontos de Atenção

1. **Atribuição não implementada no frontend**:
```python
# TODO: Adicionar no mapa mundial
# <div class="attribution">
#   Weather data from MET Norway (CC BY 4.0)
# </div>
```

2. **Coverage limitada**:
```python
# ❌ NÃO funciona para:
# - América (usar NWS ou NASA)
# - Ásia (usar NASA)
# - África (usar NASA)
# - Oceania (usar NASA)
```

---

### 3️⃣ nws_client.py (USA)

**Arquivo**: `backend/api/services/nws_client.py`

#### ✅ Pontos Fortes

```python
class NWSClient:
    """Cliente para USA Continental - Domínio Público."""
    
    # Bounding box USA Continental
    USA_BBOX = (-125.0, 24.0, -66.0, 49.0)
    
    async def get_forecast_data(...):
        # Step 1: Get grid metadata
        grid = await self._get_grid_metadata(lat, lon)
        
        # Step 2: Get forecast from grid
        data = await self._get_forecast_from_grid(grid, ...)
```

**Características**:
- ✅ **2-step API flow**: Metadata → Forecast (bem implementado)
- ✅ **Domínio Público**: Sem restrições
- ✅ **Coverage check**: Valida bbox USA
- ✅ **Dados horários**: Alta qualidade para USA
- ✅ **Sem autenticação**: Simplicidade

**Coverage USA**:
```
Longitude: -125°W (Costa Oeste) a -66°W (Costa Leste)
Latitude: 24°N (Sul da Flórida) a 49°N (Fronteira Canadá)

Inclui: Todos os 48 estados contíguos
Exclui: Alasca, Havaí, Porto Rico, territórios
```

**API Flow NWS**:
```python
# Step 1: GET /points/{lat},{lon}
{
    "properties": {
        "gridId": "OKX",
        "gridX": 35,
        "gridY": 37,
        "forecastHourly": "https://..."
    }
}

# Step 2: GET /gridpoints/{office}/{gridX},{gridY}/forecast/hourly
{
    "properties": {
        "periods": [...]
    }
}
```

#### ⚠️ Pontos de Atenção

1. **Conversões de unidade**:
```python
# NWS retorna temperaturas em Fahrenheit
temp_celsius = (temp_f - 32) * 5/9

# Vento em mph → m/s
wind_ms = wind_mph * 0.44704

# ⚠️ Verificar se conversões estão implementadas
```

2. **Rate limit**:
```python
# NWS: ~5 req/second
# ⚠️ Implementar throttling para uso intensivo
```

---

### 4️⃣ nasapower.py (LEGACY - DESCONTINUAR)

**Arquivo**: `backend/api/services/nasapower.py`

#### ❌ Problemas

```python
class NasaPowerAPI:
    """Implementação antiga - SYNC."""
    
    def __init__(self, ...):
        # ❌ Redis connection DIRETO (não usa ClimateCacheService)
        self.redis_client = Redis.from_url(REDIS_URL)
        
    def _fetch_data(self) -> Tuple[dict, list]:
        # ❌ requests.get (SYNC, bloqueia thread)
        response = requests.get(self.request, timeout=30)
        
    def _cache_key(self) -> str:
        # ❌ Chave de cache customizada (não segue padrão)
        return f"nasa_power:{self.lat}:{self.long}:{start}:{end}"
```

#### 🔴 Recomendação: MIGRAR PARA nasa_power_client.py

**Razões**:
1. **Performance**: Async é 10x mais eficiente
2. **Consistência**: Usa `ClimateCacheService` padrão
3. **Manutenção**: Design pattern moderno
4. **Pydantic**: Validação automática de dados

**Plano de Migração**:
```python
# ANTES (nasapower.py)
from backend.api.services.nasapower import NasaPowerAPI
api = NasaPowerAPI(start, end, long, lat)
data, warnings = api._fetch_data()

# DEPOIS (nasa_power_client.py)
from backend.api.services.nasa_power_client import NASAPowerClient
from backend.infrastructure.cache.climate_cache import ClimateCacheService

cache = ClimateCacheService(prefix="nasa")
client = NASAPowerClient(cache=cache)
data = await client.get_daily_data(lat, lon, start, end)
```

---

## 🔧 Integrações a Implementar

### 1. ClimateCacheService Injection

**Status**: ⚠️ Cache service existe, mas falta verificar injeção

**Verificar**:
```python
# backend/infrastructure/cache/climate_cache.py
class ClimateCacheService:
    """Cache inteligente com TTL dinâmico."""
    
    async def get(self, source, lat, lon, start, end):
        """Busca do Redis."""
        key = self._make_key(source, lat, lon, start, end)
        data = await self.redis.get(key)
        return pickle.loads(data) if data else None
    
    async def set(self, source, lat, lon, start, end, data):
        """Salva no Redis com TTL dinâmico."""
        key = self._make_key(source, lat, lon, start, end)
        ttl = self._get_ttl(start)  # 1h a 30 dias
        await self.redis.setex(key, ttl, pickle.dumps(data))
```

**TODO**: Verificar onde instanciar `ClimateCacheService` e injetar nos clientes

---

### 2. PostgreSQL Persistence

**Status**: ❌ NÃO IMPLEMENTADO

**Propósito**:
- Cache Redis: Temporário (TTL 1h - 30 dias)
- PostgreSQL: Persistência permanente

**Schema Proposto**:
```sql
CREATE TABLE climate_data (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- 'nasa_power', 'met_norway', 'nws'
    lat DECIMAL(8,6) NOT NULL,
    lon DECIMAL(9,6) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    temp_max DECIMAL(5,2),
    temp_min DECIMAL(5,2),
    temp_mean DECIMAL(5,2),
    humidity DECIMAL(5,2),
    wind_speed DECIMAL(5,2),
    solar_radiation DECIMAL(8,2),
    precipitation DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(source, lat, lon, timestamp)
);

CREATE INDEX idx_climate_coords ON climate_data(lat, lon);
CREATE INDEX idx_climate_timestamp ON climate_data(timestamp);
CREATE INDEX idx_climate_source ON climate_data(source);
```

**Fluxo com PostgreSQL**:
```
Requisição ETo
    ↓
1. Cache Redis? → SIM → Retorna
    ↓ NÃO
2. PostgreSQL? → SIM → Retorna + Atualiza Redis
    ↓ NÃO
3. API Externa → Salva PostgreSQL + Redis → Retorna
```

---

### 3. Celery Tasks

**Status**: ⚠️ Apenas `nasapower.py` (legacy) usa Celery

**Tarefas Necessárias**:

```python
# backend/infrastructure/tasks/climate_tasks.py
from celery import shared_task
from backend.api.services.nasa_power_client import NASAPowerClient
from backend.infrastructure.cache.climate_cache import ClimateCacheService

@shared_task(name="climate.fetch_nasa_power")
async def fetch_nasa_power_data(lat: float, lon: float, start: str, end: str):
    """Tarefa assíncrona para buscar dados NASA POWER."""
    cache = ClimateCacheService(prefix="nasa")
    client = NASAPowerClient(cache=cache)
    
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    
    data = await client.get_daily_data(lat, lon, start_dt, end_dt)
    
    # TODO: Salvar no PostgreSQL
    # await save_to_postgres(data)
    
    return {"status": "success", "records": len(data)}

@shared_task(name="climate.fetch_met_norway")
async def fetch_met_norway_data(lat: float, lon: float):
    """Tarefa assíncrona para buscar dados MET Norway."""
    # Similar implementation...
    pass

@shared_task(name="climate.fetch_nws")
async def fetch_nws_data(lat: float, lon: float):
    """Tarefa assíncrona para buscar dados NWS."""
    # Similar implementation...
    pass
```

**Agendamento**:
```python
# Atualização periódica para pontos fixos
from celery.schedules import crontab

app.conf.beat_schedule = {
    'update-world-climate-daily': {
        'task': 'climate.fetch_nasa_power',
        'schedule': crontab(hour=6, minute=0),  # 06:00 UTC diariamente
        'args': (lat, lon, start, end),
    },
}
```

---

## 🎯 Estratégia de Fusão de Dados

### Lógica de Seleção de Fonte

```python
def select_climate_source(lat: float, lon: float) -> str:
    """Seleciona melhor fonte para coordenadas."""
    
    # 1. Europa → MET Norway (melhor qualidade)
    if -25 <= lon <= 45 and 35 <= lat <= 72:
        return "met_norway"
    
    # 2. USA → NWS (melhor qualidade)
    if -125 <= lon <= -66 and 24 <= lat <= 49:
        return "nws"
    
    # 3. Resto do mundo → NASA POWER (global)
    return "nasa_power"
```

### Fusão Multi-fonte

Para **máxima acurácia**, combinar fontes disponíveis:

```python
async def get_fused_climate_data(
    lat: float,
    lon: float,
    start: datetime,
    end: datetime
) -> List[ClimateData]:
    """Fusão inteligente de múltiplas fontes."""
    
    sources = []
    
    # Tenta todas as fontes aplicáveis
    if is_in_europe(lat, lon):
        met_data = await met_norway_client.get_forecast_data(...)
        sources.append(("met_norway", met_data))
    
    if is_in_usa(lat, lon):
        nws_data = await nws_client.get_forecast_data(...)
        sources.append(("nws", nws_data))
    
    # NASA sempre disponível (fallback global)
    nasa_data = await nasa_client.get_daily_data(...)
    sources.append(("nasa_power", nasa_data))
    
    # Fusão: média ponderada por prioridade
    fused = merge_sources(sources, weights={
        "met_norway": 0.5,
        "nws": 0.5,
        "nasa_power": 0.3
    })
    
    return fused
```

**Peso das Fontes**:
- MET Norway (Europa): **Prioridade 1** (tempo real, alta resolução)
- NWS (USA): **Prioridade 1** (tempo real, alta resolução)
- NASA POWER (Global): **Prioridade 2** (delay 2-7 dias, backup)

---

## 📊 Métricas e Monitoramento

### Prometheus Metrics (Implementar)

```python
from prometheus_client import Counter, Histogram

# Contadores de requisições
CLIMATE_API_REQUESTS = Counter(
    'climate_api_requests_total',
    'Total de requisições a APIs climáticas',
    ['source', 'status']
)

# Latência de requisições
CLIMATE_API_DURATION = Histogram(
    'climate_api_request_duration_seconds',
    'Duração de requisições a APIs climáticas',
    ['source']
)

# Cache hit/miss
CLIMATE_CACHE_HITS = Counter(
    'climate_cache_hits_total',
    'Total de cache hits',
    ['source', 'hit']
)
```

**Uso**:
```python
with CLIMATE_API_DURATION.labels(source="nasa_power").time():
    data = await client.get_daily_data(...)
    CLIMATE_API_REQUESTS.labels(source="nasa_power", status="success").inc()
```

---

## ✅ Checklist de Implementação

### Curto Prazo (Sprint Atual)

- [ ] **1. Migrar de nasapower.py → nasa_power_client.py**
  - [ ] Atualizar imports em todos os módulos
  - [ ] Remover `backend/api/services/nasapower.py`
  - [ ] Testar compatibilidade

- [ ] **2. Implementar ClimateCacheService injection**
  - [ ] Criar factory function para clientes
  - [ ] Injetar cache em `nasa_power_client`
  - [ ] Injetar cache em `met_norway_client`
  - [ ] Injetar cache em `nws_client`

- [ ] **3. Adicionar atribuição MET Norway no frontend**
  ```html
  <div class="data-attribution">
    Weather data from MET Norway (CC BY 4.0)
  </div>
  ```

- [ ] **4. Implementar seleção automática de fonte**
  ```python
  source = select_climate_source(lat, lon)
  client = get_climate_client(source)
  ```

### Médio Prazo

- [ ] **5. Implementar PostgreSQL persistence**
  - [ ] Criar migrations para tabela `climate_data`
  - [ ] Implementar DAOs de leitura/escrita
  - [ ] Adicionar camada PostgreSQL no fluxo de cache

- [ ] **6. Criar Celery tasks para clima**
  - [ ] Task `climate.fetch_nasa_power`
  - [ ] Task `climate.fetch_met_norway`
  - [ ] Task `climate.fetch_nws`
  - [ ] Agendamento diário via Celery Beat

- [ ] **7. Implementar fusão multi-fonte**
  - [ ] Algoritmo de merge com pesos
  - [ ] Validação cruzada entre fontes
  - [ ] Detecção de outliers

### Longo Prazo

- [ ] **8. Adicionar métricas Prometheus**
  - [ ] Contadores de requisições
  - [ ] Histogramas de latência
  - [ ] Cache hit rates

- [ ] **9. Implementar rate limiting**
  - [ ] Throttling por fonte
  - [ ] Queue de requisições pendentes
  - [ ] Backoff exponencial

- [ ] **10. Dashboard de qualidade de dados**
  - [ ] Comparação entre fontes
  - [ ] Gaps de dados
  - [ ] Latência por fonte

---

## 📚 Documentação e Boas Práticas

### ✅ Pontos Fortes Atuais

1. **Docstrings completas**: Todos os métodos documentados
2. **Type hints**: Tipagem forte com Pydantic
3. **Error handling**: Try-catch com logging
4. **Health checks**: Métodos de verificação de API
5. **Coverage info**: Métodos `get_coverage_info()`

### 🔧 Melhorias Sugeridas

1. **Unit tests**:
```python
# tests/api/services/test_nasa_power_client.py
@pytest.mark.asyncio
async def test_nasa_power_cache_hit(mock_redis):
    cache = ClimateCacheService()
    client = NASAPowerClient(cache=cache)
    
    # Mock cache hit
    mock_redis.get.return_value = pickle.dumps([...])
    
    data = await client.get_daily_data(...)
    assert len(data) > 0
    assert mock_redis.get.called
```

2. **Integration tests**:
```python
@pytest.mark.integration
async def test_nasa_power_real_api():
    client = NASAPowerClient()
    data = await client.get_daily_data(
        lat=-15.7939, lon=-47.8828,
        start=datetime(2024, 10, 1),
        end=datetime(2024, 10, 7)
    )
    assert len(data) == 7  # 7 dias
```

3. **API mocks para testes**:
```python
# tests/fixtures/nasa_power_responses.py
MOCK_NASA_RESPONSE = {
    "properties": {
        "parameter": {
            "T2M_MAX": {"20241001": 25.5, ...},
            "T2M_MIN": {"20241001": 15.2, ...},
            ...
        }
    }
}
```

---

## 🎓 Referências

### APIs Oficiais

- **NASA POWER**: https://power.larc.nasa.gov/docs/services/api/
- **MET Norway**: https://api.met.no/weatherapi/locationforecast/2.0/documentation
- **NWS**: https://www.weather.gov/documentation/services-web-api

### Licenças

- **NASA POWER**: Domínio Público (Public Domain)
- **MET Norway**: CC BY 4.0 (Creative Commons Attribution 4.0)
- **NWS**: Domínio Público (US Government)

### FAO-56 Evapotranspiration

- Allen, R.G., et al. (1998). "Crop evapotranspiration - Guidelines for computing crop water requirements". FAO Irrigation and Drainage Paper 56.

---

## 🚀 Próximos Passos Imediatos

1. **Revisar este documento com a equipe**
2. **Priorizar itens do checklist**
3. **Criar issues no GitHub para cada task**
4. **Definir sprint para implementação**

**Responsável**: Equipe Backend  
**Deadline**: Sprint atual + 2 sprints

---

**Gerado em**: {{ datetime.now().isoformat() }}  
**Versão**: 1.0
