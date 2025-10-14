"""
Seletor inteligente de fonte climática baseado em coordenadas geográficas.

Usa bounding boxes para decidir automaticamente a melhor API climática
para cada localização, priorizando fontes regionais de alta qualidade.

Estratégia de Seleção:
    1. Europa → MET Norway (melhor qualidade, tempo real)
    2. USA → NWS (melhor qualidade, tempo real)
    3. Global → NASA POWER (fallback universal, delay 2-7 dias)

Uso:
    from backend.api.services.climate_source_selector import ClimateSourceSelector
    
    # Seleção automática
    source = ClimateSourceSelector.select_source(lat=48.8566, lon=2.3522)
    # → "met_norway"
    
    # Obter cliente configurado
    client = ClimateSourceSelector.get_client(lat=48.8566, lon=2.3522)
    data = await client.get_forecast_data(...)
"""

from typing import Literal, Union

from loguru import logger

from backend.api.services.climate_factory import ClimateClientFactory
from backend.api.services.met_norway_client import METNorwayClient
from backend.api.services.nasa_power_client import NASAPowerClient
from backend.api.services.nws_client import NWSClient

# Type hints para fontes climáticas
ClimateSource = Literal["nasa_power", "met_norway", "nws"]
ClimateClient = Union[NASAPowerClient, METNorwayClient, NWSClient]


class ClimateSourceSelector:
    """
    Seletor inteligente de fonte climática.
    
    Determina automaticamente a melhor API para buscar dados climáticos
    baseado nas coordenadas geográficas fornecidas.
    
    Bounding Boxes:
        - Europa: -25°W a 45°E, 35°N a 72°N (MET Norway)
        - USA: -125°W a -66°W, 24°N a 49°N (NWS)
        - Global: Qualquer coordenada (NASA POWER)
    
    Prioridades:
        1. Fontes regionais (MET Norway, NWS): Tempo real, alta qualidade
        2. Fonte global (NASA POWER): Cobertura universal, delay 2-7 dias
    """
    
    # Bounding boxes das fontes regionais
    # Formato: (lon_min, lat_min, lon_max, lat_max) = (W, S, E, N)
    
    EUROPE_BBOX = (-25.0, 35.0, 45.0, 72.0)
    """
    Bounding box Europa (MET Norway).
    
    Cobertura:
        Longitude: -25°W (Islândia) a 45°E (Rússia Ocidental)
        Latitude: 35°N (Mediterrâneo) a 72°N (Norte da Noruega)
    
    Países incluídos:
        Noruega, Suécia, Finlândia, Dinamarca, Islândia, UK, Irlanda,
        França, Alemanha, Espanha, Itália, Polônia, Holanda, Bélgica,
        Áustria, Suíça, Portugal, Grécia, etc.
    """
    
    USA_BBOX = (-125.0, 24.0, -66.0, 49.0)
    """
    Bounding box USA Continental (NWS).
    
    Cobertura:
        Longitude: -125°W (Costa Oeste) a -66°W (Costa Leste)
        Latitude: 24°N (Sul da Flórida) a 49°N (Fronteira Canadá)
    
    Estados incluídos:
        Todos os 48 estados contíguos
    
    Excluídos:
        Alasca, Havaí, Porto Rico, territórios
    """
    
    @classmethod
    def select_source(cls, lat: float, lon: float) -> ClimateSource:
        """
        Seleciona melhor fonte climática para coordenadas.
        
        Algoritmo de seleção:
        1. Verifica se está na Europa → MET Norway
        2. Verifica se está no USA → NWS
        3. Fallback → NASA POWER (cobertura global)
        
        Args:
            lat: Latitude (-90 a 90)
            lon: Longitude (-180 a 180)
        
        Returns:
            Nome da fonte recomendada: "met_norway", "nws" ou "nasa_power"
            
        Exemplo:
            # Paris, França
            source = ClimateSourceSelector.select_source(48.8566, 2.3522)
            # → "met_norway"
            
            # Nova York, USA
            source = ClimateSourceSelector.select_source(40.7128, -74.0060)
            # → "nws"
            
            # Brasília, Brasil
            source = ClimateSourceSelector.select_source(-15.7939, -47.8828)
            # → "nasa_power"
        """
        # Prioridade 1: Europa (MET Norway)
        if cls._is_in_europe(lat, lon):
            logger.debug(
                f"📍 Coordenadas ({lat}, {lon}) na Europa → MET Norway"
            )
            return "met_norway"
        
        # Prioridade 2: USA (NWS)
        if cls._is_in_usa(lat, lon):
            logger.debug(
                f"📍 Coordenadas ({lat}, {lon}) no USA → NWS"
            )
            return "nws"
        
        # Fallback: Global (NASA POWER)
        logger.debug(
            f"📍 Coordenadas ({lat}, {lon}) fora de regiões especiais → NASA POWER"
        )
        return "nasa_power"
    
    @classmethod
    def _is_in_europe(cls, lat: float, lon: float) -> bool:
        """
        Verifica se coordenadas estão no bbox Europa.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            True se dentro do bbox MET Norway
        """
        lon_min, lat_min, lon_max, lat_max = cls.EUROPE_BBOX
        return (lon_min <= lon <= lon_max) and (lat_min <= lat <= lat_max)
    
    @classmethod
    def _is_in_usa(cls, lat: float, lon: float) -> bool:
        """
        Verifica se coordenadas estão no bbox USA Continental.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            True se dentro do bbox NWS
        """
        lon_min, lat_min, lon_max, lat_max = cls.USA_BBOX
        return (lon_min <= lon <= lon_max) and (lat_min <= lat <= lat_max)
    
    @classmethod
    def get_client(cls, lat: float, lon: float) -> ClimateClient:
        """
        Retorna cliente apropriado para coordenadas.
        
        Combina select_source() com ClimateClientFactory para
        retornar cliente já configurado e pronto para uso.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Cliente climático configurado (NASAPowerClient, METNorwayClient ou NWSClient)
            
        Exemplo:
            # Obter cliente automático para Paris
            client = ClimateSourceSelector.get_client(
                lat=48.8566, lon=2.3522
            )
            # → METNorwayClient com cache injetado
            
            data = await client.get_forecast_data(...)
            await client.close()
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
        
        Útil para fusão multi-fonte ou validação cruzada.
        
        Lógica:
        - NASA POWER sempre disponível (cobertura global)
        - MET Norway se na Europa
        - NWS se no USA
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Lista de fontes aplicáveis, ordenadas por prioridade
            
        Exemplo:
            # Paris (Europa)
            sources = ClimateSourceSelector.get_all_sources(48.8566, 2.3522)
            # → ["met_norway", "nasa_power"]
            
            # Brasília (apenas global)
            sources = ClimateSourceSelector.get_all_sources(-15.7939, -47.8828)
            # → ["nasa_power"]
            
            # Nova York (USA)
            sources = ClimateSourceSelector.get_all_sources(40.7128, -74.0060)
            # → ["nws", "nasa_power"]
        """
        sources = []
        
        # Fontes regionais (alta prioridade)
        if cls._is_in_europe(lat, lon):
            sources.append("met_norway")
        
        if cls._is_in_usa(lat, lon):
            sources.append("nws")
        
        # NASA POWER sempre disponível (fallback global)
        sources.append("nasa_power")
        
        logger.debug(
            f"📍 Fontes disponíveis para ({lat}, {lon}): {sources}"
        )
        
        return sources
    
    @classmethod
    def get_coverage_info(cls, lat: float, lon: float) -> dict:
        """
        Retorna informações detalhadas sobre cobertura para coordenadas.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Dict com informações de cobertura
            
        Exemplo:
            info = ClimateSourceSelector.get_coverage_info(48.8566, 2.3522)
            # {
            #     'location': {'lat': 48.8566, 'lon': 2.3522},
            #     'recommended_source': 'met_norway',
            #     'all_sources': ['met_norway', 'nasa_power'],
            #     'regional_coverage': {
            #         'europe': True,
            #         'usa': False
            #     },
            #     'source_details': {...}
            # }
        """
        recommended = cls.select_source(lat, lon)
        all_sources = cls.get_all_sources(lat, lon)
        
        return {
            'location': {'lat': lat, 'lon': lon},
            'recommended_source': recommended,
            'all_sources': all_sources,
            'regional_coverage': {
                'europe': cls._is_in_europe(lat, lon),
                'usa': cls._is_in_usa(lat, lon)
            },
            'source_details': {
                'met_norway': {
                    'bbox': cls.EUROPE_BBOX,
                    'description': 'Europa: -25°W a 45°E, 35°N a 72°N',
                    'quality': 'high',
                    'realtime': True
                },
                'nws': {
                    'bbox': cls.USA_BBOX,
                    'description': 'USA: -125°W a -66°W, 24°N a 49°N',
                    'quality': 'high',
                    'realtime': True
                },
                'nasa_power': {
                    'bbox': None,
                    'description': 'Global coverage',
                    'quality': 'medium',
                    'realtime': False,
                    'delay_days': '2-7'
                }
            }
        }


# Exemplo de uso completo
async def example_usage():
    """Demonstra uso do seletor de fontes."""
    from datetime import datetime, timedelta

    # Exemplos de cidades em diferentes regiões
    locations = [
        {"name": "Paris, França", "lat": 48.8566, "lon": 2.3522},
        {"name": "Nova York, USA", "lat": 40.7128, "lon": -74.0060},
        {"name": "Brasília, Brasil", "lat": -15.7939, "lon": -47.8828},
        {"name": "Tóquio, Japão", "lat": 35.6762, "lon": 139.6503},
        {"name": "Oslo, Noruega", "lat": 59.9139, "lon": 10.7522},
    ]
    
    for loc in locations:
        print(f"\n📍 {loc['name']} ({loc['lat']}, {loc['lon']})")
        
        # 1. Seleção automática
        source = ClimateSourceSelector.select_source(loc['lat'], loc['lon'])
        print(f"   Fonte recomendada: {source}")
        
        # 2. Todas as fontes disponíveis
        all_sources = ClimateSourceSelector.get_all_sources(loc['lat'], loc['lon'])
        print(f"   Fontes disponíveis: {all_sources}")
        
        # 3. Obter cliente e buscar dados
        client = ClimateSourceSelector.get_client(loc['lat'], loc['lon'])
        print(f"   Cliente: {type(client).__name__}")
        
        # Buscar dados (exemplo simplificado)
        try:
            if source == "nasa_power":
                data = await client.get_daily_data(
                    lat=loc['lat'],
                    lon=loc['lon'],
                    start_date=datetime.now() - timedelta(days=7),
                    end_date=datetime.now()
                )
            else:  # met_norway ou nws
                data = await client.get_forecast_data(
                    lat=loc['lat'],
                    lon=loc['lon'],
                    start_date=datetime.now(),
                    end_date=datetime.now() + timedelta(days=3)
                )
            
            print(f"   ✅ {len(data)} registros obtidos")
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        finally:
            await client.close()
    
    # Cleanup global
    await ClimateClientFactory.close_all()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
