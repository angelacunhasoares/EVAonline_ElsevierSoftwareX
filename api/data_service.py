from fastapi import FastAPI, APIRouter, HTTPException
from prometheus_client import Counter, generate_latest
from starlette.responses import Response
from loguru import logger
from src.eto_calculator import calculate_eto_pipeline
from api.openmeteo import get_openmeteo_elevation
from celery.result import AsyncResult
from datetime import datetime
from utils.logging import configure_logging

configure_logging()

app = FastAPI()
router = APIRouter()

# Métrica do Prometheus para contar requisições
REQUESTS = Counter('evaonline_requests_total', 'Total API Requests')

@router.get("/get_elevation")
async def get_elevation(lat: float, lng: float):
    """
    Endpoint para obter elevação a partir de coordenadas usando Open-Meteo.

    Args:
        lat (float): Latitude (-90 a 90).
        lng (float): Longitude (-180 a 180).

    Returns:
        dict: Dicionário com elevação e avisos, ou erro.
    """
    REQUESTS.inc()  # Incrementa o contador
    try:
        # Validação de coordenadas
        if not (-90 <= lat <= 90):
            raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90.")
        if not (-180 <= lng <= 180):
            raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180.")

        task = get_openmeteo_elevation.apply_async(args=[lat, lng])
        elevation, warnings = task.get(timeout=15)  # Aumentado para 15 segundos
        return {"data": {"elevation": elevation}, "warnings": warnings}
    except HTTPException as e:
        logger.error(f"Erro de validação: {e.detail}")
        return {"data": None, "warnings": [], "error": e.detail}
    except Exception as e:
        logger.error(f"Erro ao obter elevação: {str(e)}")
        return {"data": None, "warnings": [], "error": str(e)}

@router.get("/metrics")
async def metrics():
    """
    Endpoint para expor métricas do Prometheus.
    """
    REQUESTS.inc()
    return Response(generate_latest(), media_type="text/plain")

@router.get("/calculate_eto")
async def calculate_eto_endpoint(
    lat: float,
    lng: float,
    elevation: float,
    database: str,
    start_date: str,
    end_date: str,
    estado: str = None,
    cidade: str = None
):
    """
    Endpoint para acionar o pipeline de cálculo de ETo.

    Args:
        lat (float): Latitude (-90 a 90).
        lng (float): Longitude (-180 a 180).
        elevation (float): Elevação em metros.
        database (str): Fonte de dados ('openmeteo_archive', 'openmeteo_forecast', 'nasa_power').
        start_date (str): Data inicial (formato YYYY-MM-DD).
        end_date (str): Data final (formato YYYY-MM-DD).
        estado (str, optional): Estado para modo MATOPIBA.
        cidade (str, optional): Cidade para modo MATOPIBA.

    Returns:
        dict: Dicionário com dados de ETo e avisos, ou erro.
    """
    REQUESTS.inc()
    try:
        # Validação de coordenadas
        if not (-90 <= lat <= 90):
            raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90.")
        if not (-180 <= lng <= 180):
            raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180.")
        
        # Validação de database
        valid_databases = ["openmeteo_archive", "openmeteo_forecast", "nasa_power"]
        if database not in valid_databases:
            raise HTTPException(status_code=400, detail=f"Invalid database. Use one of: {valid_databases}")

        # Validação de datas
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        
        if end < start:
            raise HTTPException(status_code=400, detail="End date must be after start date.")
        
        period_days = (end - start).days + 1
        if period_days < 7 or period_days > 15:
            raise HTTPException(status_code=400, detail="Period must be between 7 and 15 days.")

        # Validação para modo MATOPIBA
        if (estado or cidade) and not (estado and cidade):
            raise HTTPException(status_code=400, detail="Both estado and cidade must be provided for MATOPIBA mode.")

        result, warnings = await calculate_eto_pipeline(lat, lng, elevation, database, start_date, end_date, estado, cidade)
        return {"data": result, "warnings": warnings}
    except HTTPException as e:
        logger.error(f"Erro de validação: {e.detail}")
        return {"data": None, "warnings": [], "error": e.detail}
    except Exception as e:
        logger.error(f"Erro no endpoint calculate_eto: {str(e)}")
        return {"data": None, "warnings": [], "error": str(e)}

app.include_router(router)