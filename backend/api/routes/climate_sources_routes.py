"""
Rotas da API para gerenciamento de fontes de dados climáticos.
"""

from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.climate_source_manager import ClimateSourceManager

router = APIRouter(
    prefix="/api/v1/climate/sources",
    tags=["Climate Data Sources"]
)


class AvailableSourcesResponse(BaseModel):
    """Resposta com fontes disponíveis."""
    location: Dict[str, float] = Field(
        ..., description="Coordenadas da localização"
    )
    available_sources: List[Dict] = Field(
        ..., description="Lista de fontes disponíveis"
    )
    default_mode: str = Field(
        default="fusion", description="Modo padrão de operação"
    )
    fusion_sources: List[str] = Field(
        ..., description="IDs das fontes para fusão"
    )


class ValidationResponse(BaseModel):
    """Resposta de validação de período."""
    valid: bool = Field(..., description="Se o período é válido")
    message: str = Field(
        default=None, description="Mensagem de erro (se inválido)"
    )


class FusionWeightsResponse(BaseModel):
    """Resposta com pesos de fusão."""
    sources: List[str] = Field(..., description="IDs das fontes")
    weights: Dict[str, float] = Field(..., description="Pesos normalizados")
    total: float = Field(default=1.0, description="Soma dos pesos")


@router.get(
    "/available",
    response_model=AvailableSourcesResponse,
    summary="Lista fontes disponíveis para localização",
    description="""
    Retorna lista de fontes de dados climáticos disponíveis para uma
    coordenada específica. Detecta automaticamente cobertura regional.
    """
)
async def get_available_sources(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    long: float = Query(..., ge=-180, le=180, description="Longitude")
) -> Dict:
    """Lista fontes disponíveis para uma localização."""
    manager = ClimateSourceManager()
    sources = manager.get_available_sources(lat, long)

    # Filtra apenas fontes em tempo real para fusão padrão
    realtime_sources = [
        s["id"] for s in sources if s.get("realtime", False)
    ]

    return {
        "location": {"lat": lat, "long": long},
        "available_sources": sources,
        "default_mode": "fusion",
        "fusion_sources": realtime_sources
    }


@router.get(
    "/validate-period",
    response_model=ValidationResponse,
    summary="Valida período de datas",
    description="""
    Valida se o período selecionado está dentro das especificações:
    - Mínimo 7 dias, máximo 15 dias
    - Máximo 1 ano no passado
    - Máximo 1 dia no futuro
    """
)
async def validate_period(
    start_date: datetime = Query(..., description="Data inicial (ISO)"),
    end_date: datetime = Query(..., description="Data final (ISO)")
) -> Dict:
    """Valida período de datas."""
    manager = ClimateSourceManager()
    valid, message = manager.validate_period(start_date, end_date)

    return {
        "valid": valid,
        "message": message if not valid else "Período válido"
    }


@router.post(
    "/fusion-weights",
    response_model=FusionWeightsResponse,
    summary="Calcula pesos para fusão de dados",
    description="""
    Calcula pesos normalizados para fusão de dados baseado em
    prioridades das fontes selecionadas.
    
    ⚠️ IMPORTANTE: Fontes com licença não-comercial (ex: Open-Meteo)
    são automaticamente rejeitadas.
    """
)
async def calculate_fusion_weights(
    sources: List[str] = Query(..., description="IDs das fontes"),
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    long: float = Query(..., ge=-180, le=180, description="Longitude")
) -> Dict:
    """Calcula pesos de fusão para fontes selecionadas."""
    manager = ClimateSourceManager()

    # Valida que fontes existem e estão disponíveis
    available = manager.get_available_sources(lat, long)
    available_ids = [s["id"] for s in available]

    invalid_sources = [s for s in sources if s not in available_ids]
    if invalid_sources:
        raise HTTPException(
            status_code=400,
            detail=f"Fontes indisponíveis: {invalid_sources}"
        )

    # Calcula pesos (pode lançar ValueError se licença inválida)
    try:
        weights = manager.get_fusion_weights(sources, (lat, long))
    except ValueError as e:
        # Violação de licença (ex: Open-Meteo em fusão)
        raise HTTPException(
            status_code=403,  # Forbidden
            detail=str(e)
        )

    return {
        "sources": sources,
        "weights": weights,
        "total": sum(weights.values())
    }


@router.get(
    "/validation-info",
    summary="Informações sobre validação científica",
    description="""
    Retorna informações sobre datasets usados para validação
    científica do cálculo de ETo (Xavier, AgERA5, etc.).
    """
)
async def get_validation_info() -> Dict:
    """Retorna informações sobre datasets de validação."""
    manager = ClimateSourceManager()
    return manager.get_validation_info()


@router.get(
    "/info/{source_id}",
    summary="Detalhes de uma fonte específica",
    description="Retorna metadados completos de uma fonte de dados."
)
async def get_source_info(source_id: str) -> Dict:
    """Retorna informações detalhadas de uma fonte."""
    manager = ClimateSourceManager()

    if source_id not in manager.SOURCES_CONFIG:
        raise HTTPException(
            status_code=404,
            detail=f"Fonte '{source_id}' não encontrada"
        )

    return manager.SOURCES_CONFIG[source_id]


@router.post(
    "/download",
    summary="Baixar dados climáticos processados",
    description="""
    Endpoint para download de dados climáticos.
    ⚠️ RESTRIÇÃO: Open-Meteo (CC-BY-NC 4.0) NÃO permite download.
    Apenas fontes com licenças comerciais permitidas.
    """
)
async def download_climate_data(
    sources: List[str] = Query(..., description="IDs das fontes"),
    format: str = Query(
        default="csv",
        regex="^(csv|json|netcdf)$",
        description="Formato de saída"
    )
) -> Dict:
    """
    Prepara download de dados climáticos.
    
    Validações:
    - Open-Meteo (openmeteo) é BLOQUEADO (CC-BY-NC 4.0)
    - Outras fontes permitidas com atribuição adequada
    
    Args:
        sources: Lista de IDs de fontes
        format: Formato de saída (csv, json, netcdf)
        
    Returns:
        Dict com URL de download ou erro 403
        
    Raises:
        HTTPException 403: Se Open-Meteo incluído
        HTTPException 400: Se formato inválido
    """
    # 🔒 PROTEÇÃO CC-BY-NC: Bloqueia Open-Meteo
    if "openmeteo" in sources:
        raise HTTPException(
            status_code=403,  # Forbidden
            detail={
                "error": "download_not_allowed",
                "message": (
                    "Open-Meteo não permite download de dados. "
                    "Licença CC-BY-NC 4.0 restringe redistribuição e "
                    "uso comercial. Dados disponíveis apenas para "
                    "visualização na interface."
                ),
                "license": "CC-BY-NC 4.0",
                "allowed_uses": [
                    "Visualização na interface web",
                    "Pesquisa acadêmica (sem redistribuição)",
                    "Publicações científicas (com citação)"
                ],
                "prohibited_uses": [
                    "Download de dados brutos ou processados",
                    "Fusão com outras fontes (data fusion)",
                    "Redistribuição ou venda de dados",
                    "Integração em produtos comerciais"
                ],
                "citation": (
                    "Weather data by Open-Meteo.com "
                    "(https://open-meteo.com) - CC-BY-NC 4.0"
                ),
                "alternative_sources": [
                    "nasa_power (Domínio Público)",
                    "met_norway (CC-BY 4.0 - comercial OK)",
                    "nws_usa (Domínio Público)"
                ]
            }
        )
    
    # Validar fontes existem
    manager = ClimateSourceManager()
    invalid = [s for s in sources if s not in manager.SOURCES_CONFIG]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Fontes inválidas: {invalid}"
        )
    
    # TODO: Implementar geração de arquivo de download
    # Por enquanto, retorna URL placeholder
    return {
        "status": "ready",
        "sources": sources,
        "format": format,
        "download_url": "/api/v1/climate/download/file?id=placeholder",
        "expires_in": 3600,  # 1 hora
        "attribution_required": [
            manager.SOURCES_CONFIG[s].get("attribution", "")
            for s in sources
            if manager.SOURCES_CONFIG[s].get("attribution")
        ]
    }

