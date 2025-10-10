"""
Cliente para API MET Norway (Meteorologisk Institutt).
Licença: CC-BY 4.0 - Atribuição requerida.

MET Norway Terms of Service:
- User-Agent header obrigatório com identificação da aplicação
- Atribuição: "Data from MET Norway" em todas as visualizações
- Uso comercial permitido com atribuição

Coverage: Europa (bbox: -25°W to 45°E, 35°N to 72°N)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class METNorwayConfig(BaseModel):
    """Configuração da API MET Norway."""
    base_url: str = (
        "https://api.met.no/weatherapi/locationforecast/2.0/complete"
    )
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    user_agent: str = (
        "EVAonline/1.0 "
        "(https://github.com/angelacunhasoares/EVAonline)"
    )


class METNorwayData(BaseModel):
    """Dados retornados pela MET Norway API."""
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    temp_celsius: Optional[float] = Field(None, description="Temperatura (°C)")
    humidity_percent: Optional[float] = Field(
        None, description="Umidade relativa (%)"
    )
    wind_speed_ms: Optional[float] = Field(
        None, description="Velocidade vento (m/s)"
    )
    precipitation_mm: Optional[float] = Field(
        None, description="Precipitação (mm)"
    )
    cloud_cover_percent: Optional[float] = Field(
        None, description="Cobertura de nuvens (%)"
    )
    pressure_hpa: Optional[float] = Field(
        None, description="Pressão atmosférica (hPa)"
    )


class METNorwayClient:
    """
    Cliente para API MET Norway com cache inteligente.
    
    Features:
    - Dados meteorológicos para Europa (bbox: -25, 35, 45, 72)
    - Licença CC-BY 4.0 (atribuição obrigatória)
    - Previsão até 10 dias
    - Dados horários de alta qualidade
    - User-Agent obrigatório
    - Cache Redis integrado (opcional)
    
    Coverage:
    - Longitude: -25°W (Islândia) a 45°E (Rússia)
    - Latitude: 35°N (Mediterrâneo) a 72°N (Norte da Noruega)
    
    Attribution Required:
    "Weather data from MET Norway (CC BY 4.0)"
    
    Referência:
    https://api.met.no/weatherapi/locationforecast/2.0/documentation
    """
    
    # Bounding box Europa (lon_min, lat_min, lon_max, lat_max)
    EUROPE_BBOX = (-25.0, 35.0, 45.0, 72.0)
    
    def __init__(
        self,
        config: Optional[METNorwayConfig] = None,
        cache: Optional[any] = None
    ):
        """
        Inicializa cliente MET Norway.
        
        Args:
            config: Configuração customizada (opcional)
            cache: ClimateCacheService (opcional, injetado via DI)
        """
        self.config = config or METNorwayConfig()
        
        # Headers obrigatórios MET Norway
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/json"
        }
        
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers=headers
        )
        self.cache = cache  # Cache service opcional
    
    async def close(self):
        """Fecha conexão HTTP."""
        await self.client.aclose()
    
    def is_in_coverage(self, lat: float, lon: float) -> bool:
        """
        Verifica se coordenadas estão na cobertura Europa.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            bool: True se dentro do bbox Europa
        """
        lon_min, lat_min, lon_max, lat_max = self.EUROPE_BBOX
        return (lon_min <= lon <= lon_max) and (lat_min <= lat <= lat_max)
    
    async def get_forecast_data(
        self,
        lat: float,
        lon: float,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[METNorwayData]:
        """
        Busca dados de previsão meteorológica com cache inteligente.
        
        Fluxo:
        1. Valida cobertura (Europa bbox)
        2. Tenta buscar do cache Redis (se disponível)
        3. Se cache MISS, busca da API MET Norway
        4. Processa dados horários
        5. Salva resultado no cache
        
        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)
            start_date: Data inicial (default: agora)
            end_date: Data final (default: agora + 7 dias)
            
        Returns:
            List[METNorwayData]: Dados horários de previsão
            
        Raises:
            ValueError: Se coordenadas fora da cobertura Europa
            httpx.HTTPError: Se requisição falhar
        """
        # Validações
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude inválida: {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude inválida: {lon}")
        
        # Valida cobertura Europa
        if not self.is_in_coverage(lat, lon):
            raise ValueError(
                f"Coordenadas ({lat}, {lon}) fora da cobertura Europa. "
                f"Bbox: {self.EUROPE_BBOX}"
            )
        
        # Datas padrão
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=7)
        
        if start_date > end_date:
            raise ValueError("start_date deve ser <= end_date")
        
        # 1. Tenta buscar do cache (se disponível)
        if self.cache:
            cached_data = await self.cache.get(
                source="met_norway",
                lat=lat,
                lon=lon,
                start=start_date,
                end=end_date
            )
            if cached_data:
                logger.info(
                    f"🎯 Cache HIT: MET Norway lat={lat}, lon={lon}"
                )
                return cached_data
        
        # 2. Cache MISS - busca da API
        logger.info(f"🌐 Buscando MET Norway API: lat={lat}, lon={lon}")
        
        # Parâmetros de requisição
        params = {
            "lat": lat,
            "lon": lon
        }
        
        # Requisição com retry
        for attempt in range(self.config.retry_attempts):
            try:
                logger.info(
                    f"MET Norway request: lat={lat}, lon={lon} "
                    f"(attempt {attempt + 1})"
                )
                
                response = await self.client.get(
                    self.config.base_url,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                parsed_data = self._parse_response(
                    data, start_date, end_date
                )
                
                # 3. Salva no cache (se disponível)
                if self.cache and parsed_data:
                    await self.cache.set(
                        source="met_norway",
                        lat=lat,
                        lon=lon,
                        start=start_date,
                        end=end_date,
                        data=parsed_data
                    )
                    logger.info(
                        f"💾 Cache SAVE: MET Norway lat={lat}, lon={lon}"
                    )
                
                return parsed_data
                
            except httpx.HTTPError as e:
                logger.warning(
                    f"MET Norway request failed (attempt {attempt + 1}): {e}"
                )
                if attempt == self.config.retry_attempts - 1:
                    raise
                await self._delay_retry()
        
        return []
    
    def _parse_response(
        self,
        data: Dict,
        start_date: datetime,
        end_date: datetime
    ) -> List[METNorwayData]:
        """
        Processa resposta da API MET Norway.
        
        Estrutura da resposta:
        {
            "properties": {
                "timeseries": [
                    {
                        "time": "2024-10-09T12:00:00Z",
                        "data": {
                            "instant": {
                                "details": {
                                    "air_temperature": 15.5,
                                    "relative_humidity": 65.0,
                                    "wind_speed": 3.2,
                                    ...
                                }
                            },
                            "next_1_hours": {
                                "details": {
                                    "precipitation_amount": 0.0
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        Args:
            data: JSON response da API
            start_date: Data inicial para filtro
            end_date: Data final para filtro
        
        Returns:
            List[METNorwayData]: Dados processados
        """
        result = []
        
        try:
            timeseries = data.get("properties", {}).get("timeseries", [])
            
            for entry in timeseries:
                timestamp_str = entry.get("time")
                if not timestamp_str:
                    continue
                
                # Parse timestamp
                timestamp = datetime.fromisoformat(
                    timestamp_str.replace("Z", "+00:00")
                )
                
                # Filtra por período
                if timestamp < start_date or timestamp > end_date:
                    continue
                
                # Extrai dados instantâneos
                instant = entry.get("data", {}).get("instant", {})
                details = instant.get("details", {})
                
                # Extrai precipitação (próxima 1 hora)
                next_1h = entry.get("data", {}).get("next_1_hours", {})
                precip_details = next_1h.get("details", {})
                
                # Cria objeto METNorwayData
                met_data = METNorwayData(
                    timestamp=timestamp.isoformat(),
                    temp_celsius=details.get("air_temperature"),
                    humidity_percent=details.get("relative_humidity"),
                    wind_speed_ms=details.get("wind_speed"),
                    cloud_cover_percent=details.get("cloud_area_fraction"),
                    pressure_hpa=details.get(
                        "air_pressure_at_sea_level"
                    ),
                    precipitation_mm=precip_details.get(
                        "precipitation_amount"
                    )
                )
                
                result.append(met_data)
            
            logger.info(
                f"✅ MET Norway parsed: {len(result)} timesteps"
            )
            return result
            
        except Exception as e:
            logger.error(f"Erro ao processar resposta MET Norway: {e}")
            raise ValueError(f"Resposta MET Norway inválida: {e}")
    
    async def _delay_retry(self):
        """Aguarda antes de retry."""
        import asyncio
        await asyncio.sleep(self.config.retry_delay)
    
    async def health_check(self) -> bool:
        """
        Verifica se API MET Norway está acessível.
        
        Testa com coordenadas de Oslo (Noruega).
        
        Returns:
            bool: True se API está respondendo
        """
        try:
            # Oslo, Noruega
            params = {"lat": 59.9139, "lon": 10.7522}
            
            response = await self.client.get(
                self.config.base_url,
                params=params
            )
            response.raise_for_status()
            
            logger.info("✅ MET Norway API health check: OK")
            return True
            
        except Exception as e:
            logger.error(f"❌ MET Norway API health check failed: {e}")
            return False
    
    def get_attribution(self) -> str:
        """
        Retorna texto de atribuição obrigatório CC-BY 4.0.
        
        IMPORTANTE: Este texto deve ser exibido em todas as
        visualizações que usam dados MET Norway.
        
        Returns:
            str: Texto de atribuição
        """
        return "Weather data from MET Norway (CC BY 4.0)"
    
    def get_coverage_info(self) -> Dict[str, any]:
        """
        Retorna informações sobre cobertura geográfica.
        
        Returns:
            dict: Informações de cobertura
        """
        lon_min, lat_min, lon_max, lat_max = self.EUROPE_BBOX
        
        return {
            "region": "Europe",
            "bbox": {
                "lon_min": lon_min,
                "lat_min": lat_min,
                "lon_max": lon_max,
                "lat_max": lat_max
            },
            "description": (
                "From Iceland (-25°W) to Western Russia (45°E), "
                "Mediterranean (35°N) to Northern Norway (72°N)"
            ),
            "countries_examples": [
                "Norway", "Sweden", "Finland", "Denmark", "Iceland",
                "UK", "Ireland", "France", "Germany", "Spain",
                "Italy", "Poland", "Netherlands", "Belgium"
            ]
        }


# Factory function
def create_met_norway_client(
    cache: Optional[any] = None
) -> METNorwayClient:
    """
    Factory function para criar cliente MET Norway.
    
    Args:
        cache: ClimateCacheService opcional
    
    Returns:
        METNorwayClient configurado
    """
    return METNorwayClient(cache=cache)
