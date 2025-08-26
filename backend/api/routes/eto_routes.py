"""
Rotas internas para cálculo de ETo.
Estas rotas são consumidas pelo frontend Dash e não são expostas diretamente 
ao usuário.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union, Any
from fastapi import APIRouter, HTTPException
from loguru import logger

from backend.core.eto_calculation.eto_calculation import calculate_eto_pipeline
from backend.api.services.openmeteo import get_openmeteo_elevation
from utils.logging import configure_logging

configure_logging()

# Router interno para funções de ETo, consumido pelo Dash
eto_router = APIRouter(
    prefix="/api/internal/eto", 
    tags=["ETo Calculator Internal"]
)


@eto_router.post("/eto_calculate")
async def calculate_eto_endpoint(
    lat: float,
    lng: float,
    elevation: float,
    database: str,
    start_date: str,
    end_date: str,
    estado: Optional[str] = None,
    cidade: Optional[str] = None
) -> Dict[str, Union[Dict[str, float], List[str], str, None]]:
    """
    Endpoint interno para cálculo de ETo.
    Chamado pelo frontend quando o usuário solicita o cálculo na página de ETo.

    Args:
        lat (float): Latitude (-90 a 90)
        lng (float): Longitude (-180 a 180)
        elevation (float): Elevação em metros
        database (str): Fonte de dados ('nasa_power', 'openmeteo_forecast')
        start_date (str): Data inicial (YYYY-MM-DD)
        end_date (str): Data final (YYYY-MM-DD)
        estado (str, optional): Estado para modo MATOPIBA
        cidade (str, optional): Cidade para modo MATOPIBA

    Returns:
        Dict com resultado do cálculo de ETo e possíveis avisos
    """
    try:
        # Validação de coordenadas
        if not (-90 <= lat <= 90):
            raise HTTPException(
                status_code=400, 
                detail="A latitude deve estar entre -90 e 90 graus."
            )
        if not (-180 <= lng <= 180):
            raise HTTPException(
                status_code=400, 
                detail="A longitude deve estar entre -180 e 180 graus."
            )

        # Validação de database e modo MATOPIBA
        valid_databases = ["nasa_power", "openmeteo_forecast"]
        if database not in valid_databases:
            raise HTTPException(
                status_code=400,
                detail=f"Base de dados inválida. Use uma das opções: {valid_databases}"
            )

        # Validação específica para modo MATOPIBA
        if database == "openmeteo_forecast" and not (estado and cidade):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Para usar o Open-Meteo Forecast, é necessário fornecer "
                    "estado e cidade (Modo MATOPIBA)."
                )
            )

        # Validação de datas
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            hoje = datetime.now()

            # Verifica limite de 1 ano para trás e 1 dia para frente
            um_ano_atras = hoje - timedelta(days=365)
            amanha = hoje + timedelta(days=1)

            if start < um_ano_atras:
                raise HTTPException(
                    status_code=400,
                    detail="A data inicial não pode ser anterior a 1 ano atrás."
                )
            if end > amanha:
                raise HTTPException(
                    status_code=400,
                    detail="A data final não pode ser posterior a amanhã."
                )
            if end < start:
                raise HTTPException(
                    status_code=400,
                    detail="A data final deve ser posterior à data inicial."
                )
            
            period_days = (end - start).days + 1
            if period_days < 7 or period_days > 15:
                raise HTTPException(
                    status_code=400,
                    detail="O período deve ser entre 7 e 15 dias."
                )

        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de data inválido. Use YYYY-MM-DD."
            )

        task = calculate_eto_pipeline.apply_async(kwargs={
            "lat": lat,
            "lng": lng,
            "elevation": float(elevation),
            "database": database,
            "d_inicial": start_date,
            "d_final": end_date,
            "estado": estado if estado else "",
            "cidade": cidade if cidade else ""
        })
        result, warnings = task.get()
        return {"data": result, "warnings": warnings}

    except HTTPException as e:
        logger.error(f"Erro de validação: {e.detail}")
        return {"data": None, "warnings": [], "error": e.detail}
    except Exception as e:
        logger.error(f"Erro no endpoint calculate_eto: {str(e)}")
        return {"data": None, "warnings": [], "error": str(e)}


@eto_router.get("/elevation")
async def get_elevation(
    lat: float, 
    lng: float
) -> Dict[str, Union[Dict[str, float], List[str], str, None]]:
    """
    Endpoint para obter elevação a partir de coordenadas usando Open-Meteo.

    Args:
        lat (float): Latitude (-90 a 90).
        lng (float): Longitude (-180 a 180).

    Returns:
        Dict[str, Union[Dict[str, float], List[str], str, None]]:
            Dicionário com elevação e avisos, ou erro.
    """
    try:
        # Validação de coordenadas
        if not (-90 <= lat <= 90):
            raise HTTPException(
                status_code=400, 
                detail="A latitude deve estar entre -90 e 90 graus."
            )
        if not (-180 <= lng <= 180):
            raise HTTPException(
                status_code=400, 
                detail="A longitude deve estar entre -180 e 180 graus."
            )

        # O get_openmeteo_elevation não é uma coroutine, então não precisa do await
        elevation, warnings = get_openmeteo_elevation(lat, lng)
        return {"data": {"elevation": elevation}, "warnings": warnings}

    except HTTPException as e:
        logger.error(f"Erro de validação: {e.detail}")
        return {"data": None, "warnings": [], "error": e.detail}
    except Exception as e:
        logger.error(f"Erro ao obter elevação: {str(e)}")
        return {"data": None, "warnings": [], "error": str(e)}