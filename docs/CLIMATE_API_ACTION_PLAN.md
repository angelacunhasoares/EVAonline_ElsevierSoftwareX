# 🎯 Plano de Ação: Integração APIs Climáticas

**Data**: 13 de Outubro de 2025  
**Prioridade**: ALTA  
**Objetivo**: Integrar corretamente NASA POWER, MET Norway e NWS com Redis, PostgreSQL e Celery

---

## 🚨 Problemas Críticos Identificados

### 1. Duplicação NASA POWER
- ❌ `nasapower.py` (sync, legacy)
- ✅ `nasa_power_client.py` (async, moderno)
- **Ação**: Remover legacy

### 2. Cache não injetado
- ⚠️ Clientes aceitam cache via construtor
- ❌ Nenhum lugar injeta `ClimateCacheService`
- **Ação**: Criar factory com injeção

### 3. Sem persistência PostgreSQL
- ❌ Dados só em cache Redis (temporário)
- **Ação**: Criar tabela + DAOs

### 4. Sem tasks Celery
- ❌ Requisições síncronas sob demanda
- **Ação**: Criar tasks assíncronas

---

## 📋 Sprint 1: Fundação (1 semana)

### Task 1.1: Factory de Clientes com Cache

**Arquivo**: `backend/api/services/climate_factory.py` (NOVO)

```python
"""
Factory para criar clientes climáticos com cache injetado.
Uso: client = ClimateClientFactory.create_nasa_power()
"""

from typing import Optional
from backend.api.services.nasa_power_client import NASAPowerClient
from backend.api.services.met_norway_client import METNorwayClient
from backend.api.services.nws_client import NWSClient
from backend.infrastructure.cache.climate_cache import ClimateCacheService


class ClimateClientFactory:
    """Factory para criar clientes climáticos com dependências injetadas."""
    
    _cache_service: Optional[ClimateCacheService] = None
    
    @classmethod
    def get_cache_service(cls) -> ClimateCacheService:
        """Singleton do serviço de cache."""
        if cls._cache_service is None:
            cls._cache_service = ClimateCacheService(prefix="climate")
        return cls._cache_service
    
    @classmethod
    def create_nasa_power(cls) -> NASAPowerClient:
        """
        Cria cliente NASA POWER com cache injetado.
        
        Returns:
            NASAPowerClient configurado com ClimateCacheService
        """
        cache = cls.get_cache_service()
        return NASAPowerClient(cache=cache)
    
    @classmethod
    def create_met_norway(cls) -> METNorwayClient:
        """
        Cria cliente MET Norway com cache injetado.
        
        Returns:
            METNorwayClient configurado com ClimateCacheService
        """
        cache = cls.get_cache_service()
        return METNorwayClient(cache=cache)
    
    @classmethod
    def create_nws(cls) -> NWSClient:
        """
        Cria cliente NWS com cache injetado.
        
        Returns:
            NWSClient configurado com ClimateCacheService
        """
        cache = cls.get_cache_service()
        return NWSClient(cache=cache)
    
    @classmethod
    async def close_all(cls):
        """Fecha todas as conexões abertas."""
        if cls._cache_service and cls._cache_service.redis:
            await cls._cache_service.redis.close()


# Uso simplificado
async def example_usage():
    """Exemplo de uso da factory."""
    # Criar cliente NASA POWER
    nasa_client = ClimateClientFactory.create_nasa_power()
    
    # Buscar dados (cache automático)
    data = await nasa_client.get_daily_data(
        lat=-15.7939,
        lon=-47.8828,
        start_date=datetime(2024, 10, 1),
        end_date=datetime(2024, 10, 7)
    )
    
    # Fechar conexões
    await nasa_client.close()
    await ClimateClientFactory.close_all()
```

**Checklist Task 1.1**:
- [ ] Criar arquivo `climate_factory.py`
- [ ] Implementar singleton de cache
- [ ] Testar criação de clientes
- [ ] Atualizar imports nos módulos existentes

---

### Task 1.2: Seletor Inteligente de Fonte

**Arquivo**: `backend/api/services/climate_source_selector.py` (NOVO)

```python
"""
Seletor inteligente de fonte climática baseado em coordenadas.
Usa bounding boxes para decidir a melhor API.
"""

from typing import Literal
from backend.api.services.climate_factory import ClimateClientFactory

ClimateSource = Literal["nasa_power", "met_norway", "nws"]


class ClimateSourceSelector:
    """Seleciona melhor fonte climática para coordenadas."""
    
    # Bounding boxes
    EUROPE_BBOX = (-25.0, 35.0, 45.0, 72.0)  # MET Norway
    USA_BBOX = (-125.0, 24.0, -66.0, 49.0)   # NWS
    
    @classmethod
    def select_source(cls, lat: float, lon: float) -> ClimateSource:
        """
        Seleciona melhor fonte para coordenadas.
        
        Prioridade:
        1. MET Norway (Europa) - melhor qualidade, tempo real
        2. NWS (USA) - melhor qualidade, tempo real
        3. NASA POWER (Global) - fallback universal
        
        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)
        
        Returns:
            Nome da fonte recomendada
        """
        # Europa → MET Norway
        if cls._is_in_europe(lat, lon):
            return "met_norway"
        
        # USA → NWS
        if cls._is_in_usa(lat, lon):
            return "nws"
        
        # Global → NASA POWER
        return "nasa_power"
    
    @classmethod
    def _is_in_europe(cls, lat: float, lon: float) -> bool:
        """Verifica se coordenadas estão na Europa."""
        lon_min, lat_min, lon_max, lat_max = cls.EUROPE_BBOX
        return (lon_min <= lon <= lon_max) and (lat_min <= lat <= lat_max)
    
    @classmethod
    def _is_in_usa(cls, lat: float, lon: float) -> bool:
        """Verifica se coordenadas estão no USA Continental."""
        lon_min, lat_min, lon_max, lat_max = cls.USA_BBOX
        return (lon_min <= lon <= lon_max) and (lat_min <= lat <= lat_max)
    
    @classmethod
    def get_client(cls, lat: float, lon: float):
        """
        Retorna cliente apropriado para coordenadas.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Cliente climático (NASAPowerClient, METNorwayClient ou NWSClient)
        """
        source = cls.select_source(lat, lon)
        
        if source == "met_norway":
            return ClimateClientFactory.create_met_norway()
        elif source == "nws":
            return ClimateClientFactory.create_nws()
        else:  # nasa_power
            return ClimateClientFactory.create_nasa_power()
    
    @classmethod
    def get_all_sources(cls, lat: float, lon: float) -> list[ClimateSource]:
        """
        Retorna TODAS as fontes disponíveis para coordenadas.
        Útil para fusão multi-fonte.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Lista de fontes aplicáveis (ex: ["met_norway", "nasa_power"])
        """
        sources = ["nasa_power"]  # NASA sempre disponível
        
        if cls._is_in_europe(lat, lon):
            sources.insert(0, "met_norway")  # Prioridade
        
        if cls._is_in_usa(lat, lon):
            sources.insert(0, "nws")  # Prioridade
        
        return sources


# Uso
async def example_usage():
    """Exemplo de uso do seletor."""
    # Brasília, Brasil
    lat, lon = -15.7939, -47.8828
    
    # Selecionar fonte automática
    source = ClimateSourceSelector.select_source(lat, lon)
    print(f"Fonte recomendada: {source}")  # → "nasa_power"
    
    # Obter cliente configurado
    client = ClimateSourceSelector.get_client(lat, lon)
    data = await client.get_daily_data(lat, lon, start, end)
    
    # Paris, França
    lat, lon = 48.8566, 2.3522
    source = ClimateSourceSelector.select_source(lat, lon)
    print(f"Fonte recomendada: {source}")  # → "met_norway"
```

**Checklist Task 1.2**:
- [ ] Criar arquivo `climate_source_selector.py`
- [ ] Implementar lógica de bounding boxes
- [ ] Testar seleção para diferentes regiões
- [ ] Documentar prioridades

---

### Task 1.3: Remover Legacy nasapower.py

**Arquivos afetados**:
- `backend/api/services/nasapower.py` (DELETAR)
- Todos os imports de `nasapower` (ATUALIZAR)

**Plano de migração**:

```python
# ANTES (nasapower.py - legacy)
from backend.api.services.nasapower import NasaPowerAPI

api = NasaPowerAPI(
    start=datetime(2024, 10, 1),
    end=datetime(2024, 10, 7),
    long=-47.8828,
    lat=-15.7939
)
data, warnings = api._fetch_data()

# DEPOIS (nasa_power_client.py - novo)
from backend.api.services.climate_factory import ClimateClientFactory

client = ClimateClientFactory.create_nasa_power()
data = await client.get_daily_data(
    lat=-15.7939,
    lon=-47.8828,
    start_date=datetime(2024, 10, 1),
    end_date=datetime(2024, 10, 7)
)
await client.close()
```

**Checklist Task 1.3**:
- [ ] Buscar todos os imports de `nasapower`
  ```bash
  grep -r "from.*nasapower import" backend/
  grep -r "import nasapower" backend/
  ```
- [ ] Atualizar cada import para usar factory
- [ ] Testar funcionamento
- [ ] Deletar `nasapower.py`

---

## 📋 Sprint 2: Persistência (1 semana)

### Task 2.1: Migration PostgreSQL

**Arquivo**: `database/migrations/add_climate_data_table.sql` (NOVO)

```sql
-- Migration: Tabela de dados climáticos
-- Criado: 2025-10-13
-- Propósito: Persistência permanente de dados climáticos de múltiplas fontes

CREATE TABLE IF NOT EXISTS climate_data (
    id BIGSERIAL PRIMARY KEY,
    
    -- Identificação da fonte
    source VARCHAR(50) NOT NULL,  -- 'nasa_power', 'met_norway', 'nws'
    
    -- Localização (arredondada para 0.01° = ~1km)
    lat DECIMAL(8,6) NOT NULL,
    lon DECIMAL(9,6) NOT NULL,
    
    -- Timestamp do dado
    timestamp TIMESTAMP NOT NULL,
    
    -- Variáveis meteorológicas
    temp_max DECIMAL(5,2),        -- °C
    temp_min DECIMAL(5,2),        -- °C
    temp_mean DECIMAL(5,2),       -- °C
    humidity DECIMAL(5,2),        -- %
    wind_speed DECIMAL(5,2),      -- m/s
    solar_radiation DECIMAL(8,2), -- MJ/m²/day
    precipitation DECIMAL(8,2),   -- mm
    
    -- ETo calculado (se disponível)
    eto_fao56 DECIMAL(8,2),       -- mm/dia
    
    -- Metadados
    quality_score DECIMAL(3,2),   -- 0.00 a 1.00
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraint: 1 registro por fonte + local + timestamp
    UNIQUE(source, lat, lon, timestamp)
);

-- Índices para performance
CREATE INDEX idx_climate_coords ON climate_data(lat, lon);
CREATE INDEX idx_climate_timestamp ON climate_data(timestamp DESC);
CREATE INDEX idx_climate_source ON climate_data(source);
CREATE INDEX idx_climate_composite ON climate_data(lat, lon, timestamp);

-- Índice GiST para queries espaciais (opcional, futuro)
-- CREATE EXTENSION IF NOT EXISTS postgis;
-- ALTER TABLE climate_data ADD COLUMN geom GEOMETRY(Point, 4326);
-- CREATE INDEX idx_climate_geom ON climate_data USING GIST(geom);

-- Comentários
COMMENT ON TABLE climate_data IS 'Dados climáticos de múltiplas fontes para cálculo de ETo';
COMMENT ON COLUMN climate_data.source IS 'Fonte: nasa_power, met_norway, nws';
COMMENT ON COLUMN climate_data.quality_score IS 'Score de qualidade: 1.0=perfeito, 0.0=ruim';
COMMENT ON COLUMN climate_data.eto_fao56 IS 'Evapotranspiração FAO-56 calculada (mm/dia)';
```

**Checklist Task 2.1**:
- [ ] Criar arquivo de migration
- [ ] Testar migration em ambiente de dev
- [ ] Adicionar rollback script
- [ ] Aplicar em staging

---

### Task 2.2: DAO de Clima

**Arquivo**: `backend/database/daos/climate_dao.py` (NOVO)

```python
"""
Data Access Object para dados climáticos.
Persistência em PostgreSQL com métodos CRUD.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.database.models.climate_data import ClimateData  # Task 2.3


class ClimateDAO:
    """DAO para operações de dados climáticos no PostgreSQL."""
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa DAO com sessão do SQLAlchemy.
        
        Args:
            session: Sessão async do SQLAlchemy
        """
        self.session = session
    
    async def get_by_location_period(
        self,
        lat: float,
        lon: float,
        start: datetime,
        end: datetime,
        source: Optional[str] = None
    ) -> List[ClimateData]:
        """
        Busca dados climáticos por localização e período.
        
        Args:
            lat: Latitude (arredondada para 0.01°)
            lon: Longitude (arredondada para 0.01°)
            start: Data inicial
            end: Data final
            source: Fonte específica (opcional)
        
        Returns:
            Lista de registros ClimateData
        """
        # Arredondar coordenadas (mesmo padrão do cache)
        lat = round(lat, 2)
        lon = round(lon, 2)
        
        # Query base
        query = select(ClimateData).where(
            and_(
                ClimateData.lat == lat,
                ClimateData.lon == lon,
                ClimateData.timestamp >= start,
                ClimateData.timestamp <= end
            )
        )
        
        # Filtro de fonte (opcional)
        if source:
            query = query.where(ClimateData.source == source)
        
        # Ordenar por timestamp
        query = query.order_by(ClimateData.timestamp)
        
        result = await self.session.execute(query)
        records = result.scalars().all()
        
        logger.debug(
            f"Found {len(records)} climate records for "
            f"lat={lat}, lon={lon}, period={start} to {end}"
        )
        
        return records
    
    async def bulk_insert(self, records: List[dict]) -> int:
        """
        Insere múltiplos registros em batch (upsert).
        
        Args:
            records: Lista de dicts com dados climáticos
        
        Returns:
            Número de registros inseridos/atualizados
        """
        if not records:
            return 0
        
        try:
            # Usar INSERT ... ON CONFLICT UPDATE
            from sqlalchemy.dialects.postgresql import insert
            
            stmt = insert(ClimateData).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=['source', 'lat', 'lon', 'timestamp'],
                set_={
                    'temp_max': stmt.excluded.temp_max,
                    'temp_min': stmt.excluded.temp_min,
                    'temp_mean': stmt.excluded.temp_mean,
                    'humidity': stmt.excluded.humidity,
                    'wind_speed': stmt.excluded.wind_speed,
                    'solar_radiation': stmt.excluded.solar_radiation,
                    'precipitation': stmt.excluded.precipitation,
                    'eto_fao56': stmt.excluded.eto_fao56,
                    'quality_score': stmt.excluded.quality_score,
                    'updated_at': datetime.now()
                }
            )
            
            await self.session.execute(stmt)
            await self.session.commit()
            
            logger.info(f"Inserted/updated {len(records)} climate records")
            return len(records)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to bulk insert climate data: {e}")
            raise
    
    async def get_latest_timestamp(
        self,
        lat: float,
        lon: float,
        source: str
    ) -> Optional[datetime]:
        """
        Retorna timestamp mais recente para localização e fonte.
        Útil para decidir se precisa atualizar dados.
        
        Args:
            lat: Latitude
            lon: Longitude
            source: Fonte de dados
        
        Returns:
            Timestamp mais recente ou None
        """
        lat = round(lat, 2)
        lon = round(lon, 2)
        
        query = select(ClimateData.timestamp).where(
            and_(
                ClimateData.lat == lat,
                ClimateData.lon == lon,
                ClimateData.source == source
            )
        ).order_by(ClimateData.timestamp.desc()).limit(1)
        
        result = await self.session.execute(query)
        latest = result.scalar_one_or_none()
        
        return latest
```

**Checklist Task 2.2**:
- [ ] Criar arquivo `climate_dao.py`
- [ ] Implementar métodos CRUD
- [ ] Testar queries
- [ ] Adicionar testes unitários

---

### Task 2.3: Modelo SQLAlchemy

**Arquivo**: `backend/database/models/climate_data.py` (NOVO)

```python
"""
Modelo SQLAlchemy para tabela climate_data.
"""

from sqlalchemy import Column, BigInteger, String, Numeric, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from backend.database.base import Base


class ClimateData(Base):
    """Modelo de dados climáticos."""
    
    __tablename__ = 'climate_data'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Identificação
    source = Column(String(50), nullable=False)
    
    # Localização
    lat = Column(Numeric(8, 6), nullable=False)
    lon = Column(Numeric(9, 6), nullable=False)
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False)
    
    # Variáveis meteorológicas
    temp_max = Column(Numeric(5, 2))
    temp_min = Column(Numeric(5, 2))
    temp_mean = Column(Numeric(5, 2))
    humidity = Column(Numeric(5, 2))
    wind_speed = Column(Numeric(5, 2))
    solar_radiation = Column(Numeric(8, 2))
    precipitation = Column(Numeric(8, 2))
    
    # ETo
    eto_fao56 = Column(Numeric(8, 2))
    
    # Metadados
    quality_score = Column(Numeric(3, 2))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Constraint único
    __table_args__ = (
        UniqueConstraint('source', 'lat', 'lon', 'timestamp', name='uq_climate_record'),
    )
    
    def __repr__(self):
        return (
            f"<ClimateData(source={self.source}, "
            f"lat={self.lat}, lon={self.lon}, "
            f"timestamp={self.timestamp})>"
        )
```

**Checklist Task 2.3**:
- [ ] Criar modelo SQLAlchemy
- [ ] Adicionar ao `__init__.py` de models
- [ ] Testar criação de tabela
- [ ] Gerar migration com Alembic (se necessário)

---

## 📋 Sprint 3: Celery Tasks (1 semana)

### Task 3.1: Celery Tasks de Clima

**Arquivo**: `backend/infrastructure/tasks/climate_tasks.py` (NOVO)

```python
"""
Tarefas Celery para busca assíncrona de dados climáticos.
Executa requisições a APIs externas em background.
"""

from datetime import datetime, timedelta
from celery import shared_task
from loguru import logger

from backend.api.services.climate_factory import ClimateClientFactory
from backend.api.services.climate_source_selector import ClimateSourceSelector
from backend.database.daos.climate_dao import ClimateDAO
from backend.database.session import get_async_session


@shared_task(
    name="climate.fetch_data",
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutos
)
async def fetch_climate_data(
    self,
    lat: float,
    lon: float,
    start: str,  # ISO format
    end: str,    # ISO format
    source: str = "auto"
):
    """
    Busca dados climáticos de API externa e salva no PostgreSQL.
    
    Fluxo:
    1. Seleciona fonte apropriada (se auto)
    2. Busca da API (cache Redis automático)
    3. Salva no PostgreSQL para persistência
    
    Args:
        lat: Latitude
        lon: Longitude
        start: Data inicial (ISO format)
        end: Data final (ISO format)
        source: Fonte específica ou 'auto'
    
    Returns:
        dict: Status e estatísticas
    """
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        
        # Selecionar fonte
        if source == "auto":
            source = ClimateSourceSelector.select_source(lat, lon)
        
        logger.info(
            f"Fetching climate data: source={source}, "
            f"lat={lat}, lon={lon}, period={start} to {end}"
        )
        
        # Obter cliente apropriado
        if source == "nasa_power":
            client = ClimateClientFactory.create_nasa_power()
            data = await client.get_daily_data(lat, lon, start_dt, end_dt)
        elif source == "met_norway":
            client = ClimateClientFactory.create_met_norway()
            data = await client.get_forecast_data(lat, lon, start_dt, end_dt)
        elif source == "nws":
            client = ClimateClientFactory.create_nws()
            data = await client.get_forecast_data(lat, lon, start_dt, end_dt)
        else:
            raise ValueError(f"Unknown source: {source}")
        
        # Salvar no PostgreSQL
        async with get_async_session() as session:
            dao = ClimateDAO(session)
            
            # Converter para formato do banco
            records = [
                {
                    'source': source,
                    'lat': round(lat, 2),
                    'lon': round(lon, 2),
                    'timestamp': record.timestamp if hasattr(record, 'timestamp') 
                                 else record.date,
                    'temp_max': record.temp_max if hasattr(record, 'temp_max') 
                               else None,
                    'temp_min': record.temp_min if hasattr(record, 'temp_min') 
                               else None,
                    'temp_mean': record.temp_mean if hasattr(record, 'temp_mean') 
                                else record.temp_celsius if hasattr(record, 'temp_celsius')
                                else None,
                    'humidity': record.humidity if hasattr(record, 'humidity')
                               else record.humidity_percent if hasattr(record, 'humidity_percent')
                               else None,
                    'wind_speed': record.wind_speed if hasattr(record, 'wind_speed')
                                 else record.wind_speed_ms if hasattr(record, 'wind_speed_ms')
                                 else None,
                    'solar_radiation': record.solar_radiation if hasattr(record, 'solar_radiation')
                                      else None,
                    'precipitation': record.precipitation if hasattr(record, 'precipitation')
                                    else record.precipitation_mm if hasattr(record, 'precipitation_mm')
                                    else None,
                    'quality_score': 1.0  # TODO: calcular score real
                }
                for record in data
            ]
            
            count = await dao.bulk_insert(records)
        
        await client.close()
        
        return {
            'status': 'success',
            'source': source,
            'records': count,
            'location': {'lat': lat, 'lon': lon},
            'period': {'start': start, 'end': end}
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch climate data: {e}")
        # Retry com backoff exponencial
        raise self.retry(exc=e)


@shared_task(name="climate.update_world_grid")
async def update_world_grid_climate():
    """
    Atualiza grid mundial de dados climáticos.
    Executa diariamente para manter dados atualizados.
    
    Grid: 2° x 2° (aproximadamente 220km x 220km no equador)
    Total: ~16,000 pontos
    """
    logger.info("Starting world grid climate update")
    
    # Grid mundial (simplificado)
    # TODO: carregar de config ou banco
    grid_points = []
    for lat in range(-90, 90, 2):
        for lon in range(-180, 180, 2):
            grid_points.append((lat, lon))
    
    # Período: últimos 7 dias + próximos 7 dias
    today = datetime.now().date()
    start = today - timedelta(days=7)
    end = today + timedelta(days=7)
    
    # Disparar tasks em paralelo (Celery cuida do throttling)
    tasks = []
    for lat, lon in grid_points:
        task = fetch_climate_data.delay(
            lat=lat,
            lon=lon,
            start=start.isoformat(),
            end=end.isoformat(),
            source="auto"
        )
        tasks.append(task)
    
    logger.info(f"Dispatched {len(tasks)} climate fetch tasks")
    
    return {
        'status': 'dispatched',
        'tasks': len(tasks),
        'grid_points': len(grid_points)
    }


# Agendamento via Celery Beat
# Adicionar em celery_config.py:
"""
from celery.schedules import crontab

app.conf.beat_schedule = {
    'update-world-climate-daily': {
        'task': 'climate.update_world_grid',
        'schedule': crontab(hour=6, minute=0),  # 06:00 UTC
    },
}
"""
```

**Checklist Task 3.1**:
- [ ] Criar arquivo `climate_tasks.py`
- [ ] Implementar task `fetch_climate_data`
- [ ] Implementar task `update_world_grid_climate`
- [ ] Configurar Celery Beat schedule
- [ ] Testar execução manual
- [ ] Monitorar execução via Flower

---

## 📊 Sprint 4: Endpoint de API (3 dias)

### Task 4.1: Endpoint FastAPI para ETo

**Arquivo**: `backend/api/routes/climate.py` (NOVO)

```python
"""
Endpoints FastAPI para dados climáticos e cálculo de ETo.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.services.climate_source_selector import ClimateSourceSelector
from backend.database.daos.climate_dao import ClimateDAO
from backend.database.session import get_async_session
from backend.infrastructure.tasks.climate_tasks import fetch_climate_data

router = APIRouter(prefix="/api/climate", tags=["climate"])


class EToRequest(BaseModel):
    """Request para cálculo de ETo."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    start_date: Optional[str] = Field(None, description="Data inicial (ISO)")
    end_date: Optional[str] = Field(None, description="Data final (ISO)")
    force_refresh: bool = Field(False, description="Forçar atualização da API")


class EToResponse(BaseModel):
    """Response com dados de ETo."""
    location: dict
    source: str
    period: dict
    data: list[dict]
    cached: bool


@router.post("/eto", response_model=EToResponse)
async def get_eto_data(
    request: EToRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Retorna dados climáticos e ETo para localização.
    
    Fluxo:
    1. Verifica PostgreSQL (dados persistentes)
    2. Se não encontrar OU force_refresh=True, dispara task Celery
    3. Retorna dados disponíveis
    
    Args:
        request: Parâmetros de requisição
        session: Sessão do banco de dados
    
    Returns:
        Dados climáticos com ETo calculado
    """
    # Datas padrão
    start = (datetime.fromisoformat(request.start_date) 
             if request.start_date 
             else datetime.now() - timedelta(days=7))
    end = (datetime.fromisoformat(request.end_date) 
           if request.end_date 
           else datetime.now() + timedelta(days=7))
    
    # Selecionar fonte
    source = ClimateSourceSelector.select_source(request.lat, request.lon)
    
    # Buscar no PostgreSQL
    dao = ClimateDAO(session)
    db_records = await dao.get_by_location_period(
        lat=request.lat,
        lon=request.lon,
        start=start,
        end=end,
        source=source
    )
    
    # Verificar se precisa atualizar
    needs_update = (
        request.force_refresh or
        len(db_records) == 0 or
        _is_data_stale(db_records)
    )
    
    if needs_update:
        # Disparar task Celery (assíncrono)
        fetch_climate_data.delay(
            lat=request.lat,
            lon=request.lon,
            start=start.isoformat(),
            end=end.isoformat(),
            source=source
        )
    
    # Retornar dados disponíveis
    data = [
        {
            'timestamp': rec.timestamp.isoformat(),
            'temp_max': float(rec.temp_max) if rec.temp_max else None,
            'temp_min': float(rec.temp_min) if rec.temp_min else None,
            'temp_mean': float(rec.temp_mean) if rec.temp_mean else None,
            'humidity': float(rec.humidity) if rec.humidity else None,
            'wind_speed': float(rec.wind_speed) if rec.wind_speed else None,
            'solar_radiation': float(rec.solar_radiation) if rec.solar_radiation else None,
            'precipitation': float(rec.precipitation) if rec.precipitation else None,
            'eto_fao56': float(rec.eto_fao56) if rec.eto_fao56 else None,
        }
        for rec in db_records
    ]
    
    return EToResponse(
        location={'lat': request.lat, 'lon': request.lon},
        source=source,
        period={'start': start.isoformat(), 'end': end.isoformat()},
        data=data,
        cached=not needs_update
    )


def _is_data_stale(records) -> bool:
    """Verifica se dados estão desatualizados (>24h)."""
    if not records:
        return True
    
    latest = max(rec.updated_at for rec in records)
    age = datetime.now() - latest
    
    return age > timedelta(hours=24)


@router.get("/sources")
async def get_available_sources(lat: float, lon: float):
    """
    Retorna fontes de dados disponíveis para localização.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Lista de fontes aplicáveis
    """
    sources = ClimateSourceSelector.get_all_sources(lat, lon)
    
    return {
        'location': {'lat': lat, 'lon': lon},
        'sources': sources,
        'recommended': ClimateSourceSelector.select_source(lat, lon)
    }
```

**Checklist Task 4.1**:
- [ ] Criar endpoint `/api/climate/eto`
- [ ] Criar endpoint `/api/climate/sources`
- [ ] Testar com Postman/Thunder Client
- [ ] Adicionar documentação OpenAPI
- [ ] Integrar com frontend

---

## 🎯 Resumo de Prioridades

### 🔴 Crítico (Sprint 1)
1. ✅ Factory de clientes com cache injetado
2. ✅ Seletor inteligente de fonte
3. ✅ Remover `nasapower.py` legacy

### 🟡 Alta (Sprint 2)
4. ✅ Migration PostgreSQL
5. ✅ DAO e modelo SQLAlchemy
6. ✅ Persistência de dados

### 🟢 Média (Sprint 3)
7. ✅ Celery tasks assíncronas
8. ✅ Agendamento Celery Beat
9. ✅ Grid mundial de atualização

### 🔵 Baixa (Sprint 4)
10. ✅ Endpoint FastAPI `/api/climate/eto`
11. ✅ Integração com frontend
12. ✅ Métricas Prometheus

---

## 📈 Métricas de Sucesso

- [ ] 100% das requisições usando `nasa_power_client.py` (novo)
- [ ] 0% usando `nasapower.py` (legacy)
- [ ] Cache hit rate > 70%
- [ ] PostgreSQL com > 10,000 registros persistidos
- [ ] Celery tasks executando 24/7 sem falhas
- [ ] Latência API < 500ms (com cache)
- [ ] Cobertura de testes > 80%

---

**Próximo passo**: Implementar Task 1.1 (Factory) 🚀
