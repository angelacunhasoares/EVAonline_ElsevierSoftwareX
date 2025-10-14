"""
Factory para criar clientes climáticos com cache injetado.

Fornece método centralizado para instanciar clientes de APIs climáticas
com todas as dependências (cache Redis) corretamente injetadas.

Uso:
    from backend.api.services.climate_factory import ClimateClientFactory
    
    # Criar cliente NASA POWER
    client = ClimateClientFactory.create_nasa_power()
    data = await client.get_daily_data(lat, lon, start, end)
    await client.close()
    
    # Criar cliente MET Norway
    client = ClimateClientFactory.create_met_norway()
    data = await client.get_forecast_data(lat, lon, start, end)
    await client.close()
"""

from typing import Optional

from loguru import logger

from backend.api.services.met_norway_client import METNorwayClient
from backend.api.services.nasa_power_client import NASAPowerClient
from backend.api.services.nws_client import NWSClient
from backend.infrastructure.cache.climate_cache import ClimateCacheService


class ClimateClientFactory:
    """
    Factory para criar clientes climáticos com dependências injetadas.
    
    Features:
    - Singleton do serviço de cache (reutiliza conexão Redis)
    - Injeção automática de cache em todos os clientes
    - Método centralizado de cleanup
    
    Exemplo:
        # Usar factory ao invés de instanciar diretamente
        client = ClimateClientFactory.create_nasa_power()
        data = await client.get_daily_data(...)
    """
    
    _cache_service: Optional[ClimateCacheService] = None
    
    @classmethod
    def get_cache_service(cls) -> ClimateCacheService:
        """
        Retorna instância singleton do serviço de cache.
        
        Garante que todos os clientes compartilhem a mesma
        conexão Redis, evitando overhead de múltiplas conexões.
        
        Returns:
            ClimateCacheService: Serviço de cache compartilhado
        """
        if cls._cache_service is None:
            cls._cache_service = ClimateCacheService(prefix="climate")
            logger.info("✅ ClimateCacheService singleton criado")
        return cls._cache_service
    
    @classmethod
    def create_nasa_power(cls) -> NASAPowerClient:
        """
        Cria cliente NASA POWER com cache injetado.
        
        Features:
        - Cobertura global (qualquer coordenada)
        - Dados diários desde 1981
        - Domínio público (sem restrições)
        - Cache Redis automático
        - Delay: 2-7 dias
        
        Returns:
            NASAPowerClient: Cliente configurado e pronto para uso
            
        Exemplo:
            client = ClimateClientFactory.create_nasa_power()
            data = await client.get_daily_data(
                lat=-15.7939,
                lon=-47.8828,
                start_date=datetime(2024, 10, 1),
                end_date=datetime(2024, 10, 7)
            )
            await client.close()
        """
        cache = cls.get_cache_service()
        client = NASAPowerClient(cache=cache)
        logger.debug("🌍 NASAPowerClient criado com cache injetado")
        return client
    
    @classmethod
    def create_met_norway(cls) -> METNorwayClient:
        """
        Cria cliente MET Norway com cache injetado.
        
        Features:
        - Cobertura: Europa (-25°W a 45°E, 35°N a 72°N)
        - Dados horários de alta qualidade
        - Licença CC-BY 4.0 (atribuição obrigatória)
        - Cache Redis automático
        - Real-time (delay ~1 hora)
        
        IMPORTANTE: Exibir atribuição obrigatória:
            attribution = client.get_attribution()
            # "Weather data from MET Norway (CC BY 4.0)"
        
        Returns:
            METNorwayClient: Cliente configurado e pronto para uso
            
        Exemplo:
            client = ClimateClientFactory.create_met_norway()
            
            # Verificar cobertura
            if client.is_in_coverage(lat=48.8566, lon=2.3522):
                data = await client.get_forecast_data(
                    lat=48.8566,  # Paris
                    lon=2.3522,
                    start_date=datetime.now(),
                    end_date=datetime.now() + timedelta(days=7)
                )
            
            await client.close()
        """
        cache = cls.get_cache_service()
        client = METNorwayClient(cache=cache)
        logger.debug("🇳🇴 METNorwayClient criado com cache injetado")
        return client
    
    @classmethod
    def create_nws(cls) -> NWSClient:
        """
        Cria cliente NWS (National Weather Service) com cache injetado.
        
        Features:
        - Cobertura: USA Continental (-125°W a -66°W, 24°N a 49°N)
        - Dados horários de alta qualidade
        - Domínio público (US Government)
        - Cache Redis automático
        - Real-time (delay ~1 hora)
        
        Returns:
            NWSClient: Cliente configurado e pronto para uso
            
        Exemplo:
            client = ClimateClientFactory.create_nws()
            
            # Verificar cobertura
            if client.is_in_coverage(lat=38.8977, lon=-77.0365):
                data = await client.get_forecast_data(
                    lat=38.8977,  # Washington DC
                    lon=-77.0365,
                    start_date=datetime.now(),
                    end_date=datetime.now() + timedelta(days=7)
                )
            
            await client.close()
        """
        cache = cls.get_cache_service()
        client = NWSClient(cache=cache)
        logger.debug("🇺🇸 NWSClient criado com cache injetado")
        return client
    
    @classmethod
    async def close_all(cls):
        """
        Fecha todas as conexões abertas (Redis, HTTP clients).
        
        Deve ser chamado ao finalizar aplicação ou em cleanup
        de testes para evitar warnings de conexões não fechadas.
        
        Exemplo:
            # No shutdown da aplicação
            await ClimateClientFactory.close_all()
        """
        if cls._cache_service and cls._cache_service.redis:
            await cls._cache_service.redis.close()
            logger.info("✅ ClimateCacheService Redis connection closed")
            cls._cache_service = None


# Exemplo de uso completo
async def example_usage():
    """
    Demonstra uso completo da factory.
    
    Este exemplo mostra o fluxo típico de:
    1. Criar cliente via factory
    2. Buscar dados (cache automático)
    3. Fechar conexões
    """
    from datetime import datetime, timedelta
    
    try:
        # 1. Criar cliente NASA POWER
        nasa_client = ClimateClientFactory.create_nasa_power()
        
        # 2. Buscar dados para Brasília
        logger.info("Buscando dados climáticos para Brasília...")
        data = await nasa_client.get_daily_data(
            lat=-15.7939,
            lon=-47.8828,
            start_date=datetime(2024, 10, 1),
            end_date=datetime(2024, 10, 7)
        )
        
        logger.info(f"✅ Recebidos {len(data)} registros de NASA POWER")
        
        # 3. Exemplo com MET Norway (Europa)
        met_client = ClimateClientFactory.create_met_norway()
        
        # Verificar se está na cobertura
        if met_client.is_in_coverage(lat=48.8566, lon=2.3522):
            logger.info("Buscando dados climáticos para Paris...")
            met_data = await met_client.get_forecast_data(
                lat=48.8566,
                lon=2.3522,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=3)
            )
            
            logger.info(f"✅ Recebidos {len(met_data)} registros de MET Norway")
            
            # IMPORTANTE: Exibir atribuição obrigatória
            attribution = met_client.get_attribution()
            logger.info(f"📝 Atribuição: {attribution}")
        
        # 4. Fechar conexões individuais
        await nasa_client.close()
        await met_client.close()
        
    finally:
        # 5. Cleanup global
        await ClimateClientFactory.close_all()
        logger.info("✅ Todas as conexões fechadas")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
