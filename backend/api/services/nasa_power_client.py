"""
Cliente para API NASA POWER.
Domínio Público - Uso livre para fusão, download e comercial.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NASAPowerConfig(BaseModel):
    """Configuração da API NASA POWER."""
    base_url: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


class NASAPowerData(BaseModel):
    """Dados retornados pela NASA POWER."""
    date: str = Field(..., description="Data ISO 8601")
    temp_max: Optional[float] = Field(None, description="Temp máxima (°C)")
    temp_min: Optional[float] = Field(None, description="Temp mínima (°C)")
    temp_mean: Optional[float] = Field(None, description="Temp média (°C)")
    humidity: Optional[float] = Field(None, description="Umidade relativa (%)")
    wind_speed: Optional[float] = Field(
        None, description="Velocidade vento (m/s)"
    )
    solar_radiation: Optional[float] = Field(
        None, description="Radiação solar (MJ/m²/day)"
    )
    precipitation: Optional[float] = Field(
        None, description="Precipitação (mm/dia)"
    )


class NASAPowerClient:
    """
    Cliente para API NASA POWER com cache inteligente.
    
    Features:
    - Dados climáticos diários globais desde 1981
    - Domínio Público (uso comercial OK)
    - Delay: 2-7 dias
    - Variáveis FAO-56 completas
    - Cache Redis integrado (opcional)
    
    Referência:
    https://power.larc.nasa.gov/docs/services/api/
    """
    
    def __init__(
        self,
        config: Optional[NASAPowerConfig] = None,
        cache: Optional[any] = None
    ):
        """
        Inicializa cliente NASA POWER.
        
        Args:
            config: Configuração customizada (opcional)
            cache: ClimateCacheService (opcional, injetado via DI)
        """
        self.config = config or NASAPowerConfig()
        self.client = httpx.AsyncClient(timeout=self.config.timeout)
        self.cache = cache  # Cache service opcional
    
    async def close(self):
        """Fecha conexão HTTP."""
        await self.client.aclose()
    
    async def get_daily_data(
        self,
        lat: float,
        lon: float,
        start_date: datetime,
        end_date: datetime,
        community: str = "ag"
    ) -> List[NASAPowerData]:
        """
        Busca dados climáticos diários para um ponto com cache inteligente.
        
        Fluxo:
        1. Tenta buscar do cache Redis (se disponível)
        2. Se cache MISS, busca da API NASA POWER
        3. Salva resultado no cache para requisições futuras
        
        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)
            start_date: Data inicial
            end_date: Data final
            community: Comunidade NASA POWER (ag=agriculture)
            
        Returns:
            List[NASAPowerData]: Dados diários
            
        Raises:
            httpx.HTTPError: Se requisição falhar
            ValueError: Se parâmetros inválidos
        """
        # Validações
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude inválida: {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude inválida: {lon}")
        if start_date > end_date:
            raise ValueError("start_date deve ser <= end_date")
        
        # 1. Tenta buscar do cache (se disponível)
        if self.cache:
            cached_data = await self.cache.get(
                source="nasa_power",
                lat=lat,
                lon=lon,
                start=start_date,
                end=end_date
            )
            if cached_data:
                logger.info(
                    f"🎯 Cache HIT: NASA POWER lat={lat}, lon={lon}"
                )
                return cached_data
        
        # 2. Cache MISS - busca da API
        logger.info(f"🌐 Buscando NASA API: lat={lat}, lon={lon}")
        
        # Formatar datas (YYYYMMDD)
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        # Parâmetros de requisição
        params = {
            "parameters": ",".join([
                "T2M_MAX",        # Temp máxima 2m (°C)
                "T2M_MIN",        # Temp mínima 2m (°C)
                "T2M",            # Temp média 2m (°C)
                "RH2M",           # Umidade relativa 2m (%)
                "WS2M",           # Velocidade vento 2m (m/s)
                "ALLSKY_SFC_SW_DWN",  # Radiação solar (kWh/m²/day)
                "PRECTOTCORR"     # Precipitação (mm/dia)
            ]),
            "community": community,
            "longitude": lon,
            "latitude": lat,
            "start": start_str,
            "end": end_str,
            "format": "JSON"
        }
        
        # Requisição com retry
        for attempt in range(self.config.retry_attempts):
            try:
                logger.info(
                    f"NASA POWER request: lat={lat}, lon={lon}, "
                    f"dates={start_str} to {end_str} (attempt {attempt + 1})"
                )
                
                response = await self.client.get(
                    self.config.base_url,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                parsed_data = self._parse_response(data)
                
                # 3. Salva no cache (se disponível)
                if self.cache and parsed_data:
                    await self.cache.set(
                        source="nasa_power",
                        lat=lat,
                        lon=lon,
                        start=start_date,
                        end=end_date,
                        data=parsed_data
                    )
                    logger.info(
                        f"💾 Cache SAVE: NASA POWER lat={lat}, lon={lon}"
                    )
                
                return parsed_data
                
            except httpx.HTTPError as e:
                logger.warning(
                    f"NASA POWER request failed (attempt {attempt + 1}): {e}"
                )
                if attempt == self.config.retry_attempts - 1:
                    raise
                await self._delay_retry()
        
        raise httpx.HTTPError("NASA POWER: Todos os attempts falharam")
    
    def _parse_response(self, data: Dict) -> List[NASAPowerData]:
        """
        Parseia resposta JSON da NASA POWER.
        
        Args:
            data: Resposta JSON
            
        Returns:
            List[NASAPowerData]: Dados parseados
        """
        if "properties" not in data or "parameter" not in data["properties"]:
            raise ValueError("Resposta NASA POWER inválida (falta 'parameter')")
        
        parameters = data["properties"]["parameter"]
        
        # Extrair datas (primeira chave de qualquer parâmetro)
        first_param = next(iter(parameters.values()))
        dates = sorted(first_param.keys())
        
        results = []
        for date_str in dates:
            # Converter radiação kWh/m²/day → MJ/m²/day (1 kWh = 3.6 MJ)
            solar_kwh = parameters.get("ALLSKY_SFC_SW_DWN", {}).get(date_str)
            solar_mj = solar_kwh * 3.6 if solar_kwh is not None else None
            
            record = NASAPowerData(
                date=self._format_date(date_str),
                temp_max=parameters.get("T2M_MAX", {}).get(date_str),
                temp_min=parameters.get("T2M_MIN", {}).get(date_str),
                temp_mean=parameters.get("T2M", {}).get(date_str),
                humidity=parameters.get("RH2M", {}).get(date_str),
                wind_speed=parameters.get("WS2M", {}).get(date_str),
                solar_radiation=solar_mj,
                precipitation=parameters.get("PRECTOTCORR", {}).get(date_str)
            )
            results.append(record)
        
        logger.info(f"NASA POWER: Parseados {len(results)} registros")
        return results
    
    def _format_date(self, date_str: str) -> str:
        """
        Converte data YYYYMMDD → ISO 8601 (YYYY-MM-DD).
        
        Args:
            date_str: Data no formato YYYYMMDD
            
        Returns:
            str: Data ISO 8601
        """
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        return f"{year}-{month}-{day}"
    
    async def _delay_retry(self):
        """Delay entre tentativas de retry."""
        import asyncio
        await asyncio.sleep(self.config.retry_delay)
    
    async def get_current_delay(self) -> timedelta:
        """
        Retorna delay atual dos dados NASA POWER.
        
        Delay típico: 2-7 dias
        
        Returns:
            timedelta: Delay estimado
        """
        # NASA POWER tem delay de ~2 dias, mas pode chegar a 7
        return timedelta(days=2)
    
    async def health_check(self) -> bool:
        """
        Verifica se API está acessível.
        
        Returns:
            bool: True se API responde
        """
        try:
            # Tenta buscar 1 dia de dados para um ponto qualquer
            yesterday = datetime.now() - timedelta(days=3)
            await self.get_daily_data(
                lat=0.0,
                lon=0.0,
                start_date=yesterday,
                end_date=yesterday
            )
            return True
        except Exception as e:
            logger.error(f"NASA POWER health check failed: {e}")
            return False


# Exemplo de uso
async def example_usage():
    """Demonstra uso do cliente NASA POWER."""
    client = NASAPowerClient()
    
    try:
        # Buscar dados para Brasília
        data = await client.get_daily_data(
            lat=-15.7939,
            lon=-47.8828,
            start_date=datetime(2024, 10, 1),
            end_date=datetime(2024, 10, 7)
        )
        
        print(f"✅ NASA POWER: {len(data)} registros")
        for record in data[:3]:  # Primeiros 3
            print(f"  {record.date}: "
                  f"T={record.temp_mean}°C, "
                  f"RH={record.humidity}%, "
                  f"Solar={record.solar_radiation} MJ/m²/day")
    
    finally:
        await client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
