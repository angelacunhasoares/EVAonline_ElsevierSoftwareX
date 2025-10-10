"""
Cliente para API NWS (National Weather Service / NOAA).
Licença: US Government Public Domain - Uso livre.

NWS API Terms of Service:
- Sem autenticação necessária
- User-Agent recomendado (não obrigatório)
- Domínio público (sem restrições de uso)
- Rate limit: ~5 requests/second

Coverage: USA Continental (bbox: -125°W to -66°W, 24°N to 49°N)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NWSConfig(BaseModel):
    """Configuração da API NWS."""
    base_url: str = "https://api.weather.gov"
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    user_agent: str = (
        "EVAonline/1.0 "
        "(https://github.com/angelacunhasoares/EVAonline)"
    )


class NWSData(BaseModel):
    """Dados retornados pela NWS API."""
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    temp_celsius: Optional[float] = Field(None, description="Temperatura (°C)")
    dewpoint_celsius: Optional[float] = Field(
        None, description="Ponto de orvalho (°C)"
    )
    humidity_percent: Optional[float] = Field(
        None, description="Umidade relativa (%)"
    )
    wind_speed_ms: Optional[float] = Field(
        None, description="Velocidade vento (m/s)"
    )
    wind_direction: Optional[float] = Field(
        None, description="Direção vento (graus)"
    )
    precipitation_mm: Optional[float] = Field(
        None, description="Precipitação (mm)"
    )
    sky_cover_percent: Optional[float] = Field(
        None, description="Cobertura de nuvens (%)"
    )


class NWSClient:
    """
    Cliente para API NWS (National Weather Service) com cache inteligente.
    
    Features:
    - Dados meteorológicos para USA Continental
    - Domínio Público (sem restrições)
    - Previsão até 7 dias
    - Dados horários de alta qualidade
    - Sem autenticação necessária
    - Cache Redis integrado (opcional)
    
    Coverage:
    - Longitude: -125°W (Costa Oeste) a -66°W (Costa Leste)
    - Latitude: 24°N (Sul da Florida) a 49°N (Fronteira Canadá)
    
    API Flow:
    1. GET /points/{lat},{lon} → retorna grid office e coordinates
    2. GET /gridpoints/{office}/{gridX},{gridY}/forecast/hourly
       → retorna previsão horária
    
    Referência:
    https://www.weather.gov/documentation/services-web-api
    """
    
    # Bounding box USA Continental (lon_min, lat_min, lon_max, lat_max)
    USA_BBOX = (-125.0, 24.0, -66.0, 49.0)
    
    def __init__(
        self,
        config: Optional[NWSConfig] = None,
        cache: Optional[any] = None
    ):
        """
        Inicializa cliente NWS.
        
        Args:
            config: Configuração customizada (opcional)
            cache: ClimateCacheService (opcional, injetado via DI)
        """
        self.config = config or NWSConfig()
        
        # Headers recomendados NWS
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/geo+json"
        }
        
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers=headers,
            follow_redirects=True
        )
        self.cache = cache  # Cache service opcional
    
    async def close(self):
        """Fecha conexão HTTP."""
        await self.client.aclose()
    
    def is_in_coverage(self, lat: float, lon: float) -> bool:
        """
        Verifica se coordenadas estão na cobertura USA Continental.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            bool: True se dentro do bbox USA
        """
        lon_min, lat_min, lon_max, lat_max = self.USA_BBOX
        return (lon_min <= lon <= lon_max) and (lat_min <= lat <= lat_max)
    
    async def get_forecast_data(
        self,
        lat: float,
        lon: float,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[NWSData]:
        """
        Busca dados de previsão meteorológica com cache inteligente.
        
        Fluxo NWS API (2 steps):
        1. GET /points/{lat},{lon} → metadata (office, grid)
        2. GET /gridpoints/{office}/{gridX},{gridY}/forecast/hourly
           → forecast data
        
        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)
            start_date: Data inicial (default: agora)
            end_date: Data final (default: agora + 7 dias)
            
        Returns:
            List[NWSData]: Dados horários de previsão
            
        Raises:
            ValueError: Se coordenadas fora da cobertura USA
            httpx.HTTPError: Se requisição falhar
        """
        # Validações
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude inválida: {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude inválida: {lon}")
        
        # Valida cobertura USA
        if not self.is_in_coverage(lat, lon):
            raise ValueError(
                f"Coordenadas ({lat}, {lon}) fora da cobertura USA. "
                f"Bbox: {self.USA_BBOX}"
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
                source="nws",
                lat=lat,
                lon=lon,
                start=start_date,
                end=end_date
            )
            if cached_data:
                logger.info(
                    f"🎯 Cache HIT: NWS lat={lat}, lon={lon}"
                )
                return cached_data
        
        # 2. Cache MISS - busca da API
        logger.info(f"🌐 Buscando NWS API: lat={lat}, lon={lon}")
        
        # Step 1: Get grid metadata
        grid_metadata = await self._get_grid_metadata(lat, lon)
        
        # Step 2: Get forecast data
        parsed_data = await self._get_forecast_from_grid(
            grid_metadata,
            start_date,
            end_date
        )
        
        # 3. Salva no cache (se disponível)
        if self.cache and parsed_data:
            await self.cache.set(
                source="nws",
                lat=lat,
                lon=lon,
                start=start_date,
                end=end_date,
                data=parsed_data
            )
            logger.info(
                f"💾 Cache SAVE: NWS lat={lat}, lon={lon}"
            )
        
        return parsed_data
    
    async def _get_grid_metadata(
        self,
        lat: float,
        lon: float
    ) -> Dict:
        """
        Busca metadata do grid NWS para coordenadas.
        
        Endpoint: GET /points/{lat},{lon}
        
        Retorna:
        {
            "properties": {
                "gridId": "OKX",
                "gridX": 35,
                "gridY": 37,
                "forecast": "https://api.weather.gov/gridpoints/OKX/35,37/forecast",
                "forecastHourly": "https://..."
            }
        }
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            dict: Metadata do grid
        """
        points_url = f"{self.config.base_url}/points/{lat},{lon}"
        
        for attempt in range(self.config.retry_attempts):
            try:
                logger.info(
                    f"NWS metadata request: {points_url} "
                    f"(attempt {attempt + 1})"
                )
                
                response = await self.client.get(points_url)
                response.raise_for_status()
                
                data = response.json()
                properties = data.get("properties", {})
                
                if not properties.get("forecastHourly"):
                    raise ValueError(
                        "NWS metadata inválida (sem forecastHourly)"
                    )
                
                return properties
                
            except httpx.HTTPError as e:
                logger.warning(
                    f"NWS metadata failed (attempt {attempt + 1}): {e}"
                )
                if attempt == self.config.retry_attempts - 1:
                    raise
                await self._delay_retry()
        
        raise ValueError("Failed to get NWS grid metadata")
    
    async def _get_forecast_from_grid(
        self,
        grid_metadata: Dict,
        start_date: datetime,
        end_date: datetime
    ) -> List[NWSData]:
        """
        Busca dados de previsão usando grid metadata.
        
        Args:
            grid_metadata: Metadata retornada por _get_grid_metadata
            start_date: Data inicial
            end_date: Data final
        
        Returns:
            List[NWSData]: Dados processados
        """
        forecast_url = grid_metadata.get("forecastHourly")
        
        if not forecast_url:
            raise ValueError("Grid metadata sem URL de forecast")
        
        for attempt in range(self.config.retry_attempts):
            try:
                logger.info(
                    f"NWS forecast request: {forecast_url} "
                    f"(attempt {attempt + 1})"
                )
                
                response = await self.client.get(forecast_url)
                response.raise_for_status()
                
                data = response.json()
                return self._parse_forecast_response(
                    data, start_date, end_date
                )
                
            except httpx.HTTPError as e:
                logger.warning(
                    f"NWS forecast failed (attempt {attempt + 1}): {e}"
                )
                if attempt == self.config.retry_attempts - 1:
                    raise
                await self._delay_retry()
        
        return []
    
    def _parse_forecast_response(
        self,
        data: Dict,
        start_date: datetime,
        end_date: datetime
    ) -> List[NWSData]:
        """
        Processa resposta de forecast da API NWS.
        
        Estrutura:
        {
            "properties": {
                "periods": [
                    {
                        "number": 1,
                        "name": "Tonight",
                        "startTime": "2024-10-09T18:00:00-04:00",
                        "endTime": "2024-10-09T19:00:00-04:00",
                        "temperature": 68,
                        "temperatureUnit": "F",
                        "windSpeed": "5 mph",
                        "windDirection": "SW",
                        "shortForecast": "Partly Cloudy",
                        "probabilityOfPrecipitation": {"value": 20}
                    }
                ]
            }
        }
        
        Args:
            data: JSON response
            start_date: Data inicial
            end_date: Data final
        
        Returns:
            List[NWSData]: Dados processados
        """
        result = []
        
        try:
            periods = data.get("properties", {}).get("periods", [])
            
            for period in periods:
                start_time_str = period.get("startTime")
                if not start_time_str:
                    continue
                
                # Parse timestamp
                timestamp = datetime.fromisoformat(start_time_str)
                
                # Filtra por período
                if timestamp < start_date or timestamp > end_date:
                    continue
                
                # Temperatura (converte F → C)
                temp_f = period.get("temperature")
                temp_c = None
                if temp_f is not None:
                    temp_c = (temp_f - 32) * 5/9
                
                # Wind speed (converte mph → m/s)
                wind_str = period.get("windSpeed", "")
                wind_ms = None
                if "mph" in wind_str:
                    try:
                        mph = float(wind_str.split()[0])
                        wind_ms = mph * 0.44704  # mph to m/s
                    except (ValueError, IndexError):
                        pass
                
                # Precipitação (probabilidade → estimativa)
                precip_prob = period.get(
                    "probabilityOfPrecipitation", {}
                ).get("value", 0)
                precip_mm = None
                if precip_prob and precip_prob > 30:
                    # Estimativa simples: prob > 30% → 1-5mm
                    precip_mm = (precip_prob / 100) * 5
                
                # Cria objeto NWSData
                nws_data = NWSData(
                    timestamp=timestamp.isoformat(),
                    temp_celsius=temp_c,
                    dewpoint_celsius=period.get("dewpoint", {}).get(
                        "value"
                    ),
                    humidity_percent=period.get("relativeHumidity", {}).get(
                        "value"
                    ),
                    wind_speed_ms=wind_ms,
                    wind_direction=None,  # TODO: parse direction
                    precipitation_mm=precip_mm,
                    sky_cover_percent=None  # Não disponível
                )
                
                result.append(nws_data)
            
            logger.info(
                f"✅ NWS parsed: {len(result)} periods"
            )
            return result
            
        except Exception as e:
            logger.error(f"Erro ao processar resposta NWS: {e}")
            raise ValueError(f"Resposta NWS inválida: {e}")
    
    async def _delay_retry(self):
        """Aguarda antes de retry."""
        import asyncio
        await asyncio.sleep(self.config.retry_delay)
    
    async def health_check(self) -> bool:
        """
        Verifica se API NWS está acessível.
        
        Testa com coordenadas de Washington DC.
        
        Returns:
            bool: True se API está respondendo
        """
        try:
            # Washington DC
            points_url = (
                f"{self.config.base_url}/points/38.8977,-77.0365"
            )
            
            response = await self.client.get(points_url)
            response.raise_for_status()
            
            logger.info("✅ NWS API health check: OK")
            return True
            
        except Exception as e:
            logger.error(f"❌ NWS API health check failed: {e}")
            return False
    
    def get_attribution(self) -> str:
        """
        Retorna texto de atribuição (opcional, domínio público).
        
        Returns:
            str: Texto de atribuição
        """
        return "Weather data from National Weather Service (NOAA)"
    
    def get_coverage_info(self) -> Dict[str, any]:
        """
        Retorna informações sobre cobertura geográfica.
        
        Returns:
            dict: Informações de cobertura
        """
        lon_min, lat_min, lon_max, lat_max = self.USA_BBOX
        
        return {
            "region": "USA Continental",
            "bbox": {
                "lon_min": lon_min,
                "lat_min": lat_min,
                "lon_max": lon_max,
                "lat_max": lat_max
            },
            "description": (
                "West Coast (-125°W) to East Coast (-66°W), "
                "Southern Florida (24°N) to Canadian border (49°N)"
            ),
            "states_covered": [
                "All 48 contiguous states",
                "Excludes: Alaska, Hawaii, Puerto Rico, territories"
            ]
        }


# Factory function
def create_nws_client(
    cache: Optional[any] = None
) -> NWSClient:
    """
    Factory function para criar cliente NWS.
    
    Args:
        cache: ClimateCacheService opcional
    
    Returns:
        NWSClient configurado
    """
    return NWSClient(cache=cache)
