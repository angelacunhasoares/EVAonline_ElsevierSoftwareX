from fastapi import FastAPI, APIRouter
from prometheus_client import Counter, generate_latest
from starlette.responses import Response
from loguru import logger
from src.eto_calculator import calculate_eto_pipeline

from utils.logging import configure_logging
configure_logging()

app = FastAPI()
router = APIRouter()

# Métrica do Prometheus para contar requisições
REQUESTS = Counter('evaonline_requests_total', 'Total API Requests')


@router.get("/metrics")
async def metrics():
    REQUESTS.inc()  # Incrementa o contador a cada requisição
    return Response(generate_latest(), media_type="text/plain")


@app.get("/calculate_eto")
async def calculate_eto_endpoint(lat: float, lng: float, elevation: float, database: str, start_date: str, end_date: str, estado: str = None, cidade: str = None):
    """
    Endpoint para acionar o pipeline de cálculo de ETo.
    """
    try:
        result, warnings = await calculate_eto_pipeline(lat, lng, elevation, database, start_date, end_date, estado, cidade)
        return {"data": result, "warnings": warnings}
    except Exception as e:
        logger.error(f"Erro no endpoint calculate_eto: {str(e)}")
        return {"error": str(e)}


app.include_router(router)