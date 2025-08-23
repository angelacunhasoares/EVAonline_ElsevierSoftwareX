from fastapi import FastAPI, APIRouter, HTTPException
from prometheus_client import Counter, generate_latest
from starlette.responses import Response
from loguru import logger
from typing import Optional
from src.eto_calculator import calculate_eto_pipeline
from api.openmeteo import get_openmeteo_elevation
from celery.result import AsyncResult
from datetime import datetime, timedelta
from utils.logging import configure_logging
from utils.get_translations import get_translations
import tenacity
import json
import redis
import os

configure_logging()

# Configuração do Redis
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
try:
    redis_client = redis.from_url(redis_url)
    logger.info(f"Conectado ao Redis em {redis_url}")
except Exception as e:
    logger.error(f"Erro ao conectar ao Redis: {e}")
    redis_client = None

app = FastAPI()
router = APIRouter()

# Métrica do Prometheus para contar requisições
REQUESTS = Counter('evaonline_requests_total', 'Total API Requests')

@router.get("/health")
async def health_check():
    """
    Endpoint para verificação de saúde da API.
    """
    return {"status": "ok", "service": "evaonline-api"}

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
    REQUESTS.inc()
    try:
        # Validação de coordenadas
        if not (-90 <= lat <= 90):
            raise HTTPException(status_code=400, detail="A latitude deve estar entre -90 e 90 graus.")
        if not (-180 <= lng <= 180):
            raise HTTPException(status_code=400, detail="A longitude deve estar entre -180 e 180 graus.")
        
        @tenacity.retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_exponential(multiplier=1, min=4, max=10))
        def run_task():
            return get_openmeteo_elevation(lat, lng)
        
        elevation, warnings = run_task()
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
    estado: Optional[str] = None,
    cidade: Optional[str] = None
):
    """
    Endpoint para acionar o pipeline de cálculo de ETo.

    Args:
        lat (float): Latitude (-90 a 90).
        lng (float): Longitude (-180 a 180).
        elevation (float): Elevação em metros.
        database (str): Fonte de dados ('nasa_power', 'openmeteo_forecast').
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
            raise HTTPException(status_code=400, detail="A latitude deve estar entre -90 e 90 graus.")
        if not (-180 <= lng <= 180):
            raise HTTPException(status_code=400, detail="A longitude deve estar entre -180 e 180 graus.")
        
        # Validação de database e modo MATOPIBA
        valid_databases = ["nasa_power", "openmeteo_forecast"]
        if database not in valid_databases:
            raise HTTPException(status_code=400, detail=f"Base de dados inválida. Use uma das opções: {valid_databases}")

        # Validação específica para modo MATOPIBA
        if database == "openmeteo_forecast":
            if not (estado and cidade):
                raise HTTPException(
                    status_code=400, 
                    detail="Para usar o Open-Meteo Forecast, é necessário fornecer estado e cidade (Modo MATOPIBA)."
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
                raise HTTPException(status_code=400, detail="A data inicial não pode ser anterior a 1 ano atrás.")
            if end > amanha:
                raise HTTPException(status_code=400, detail="A data final não pode ser posterior a amanhã.")
            
            if end < start:
                raise HTTPException(status_code=400, detail="A data final deve ser posterior à data inicial.")
            
            period_days = (end - start).days + 1
            if period_days < 7 or period_days > 15:
                raise HTTPException(status_code=400, detail="O período deve ser entre 7 e 15 dias.")

        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD.")

        result, warnings = await calculate_eto_pipeline(lat, lng, elevation, database, start_date, end_date, estado, cidade)
        return {"data": result, "warnings": warnings}
    except HTTPException as e:
        logger.error(f"Erro de validação: {e.detail}")
        return {"data": None, "warnings": [], "error": e.detail}
    except Exception as e:
        logger.error(f"Erro no endpoint calculate_eto: {str(e)}")
        return {"data": None, "warnings": [], "error": str(e)}

@router.get("/api/translations/{lang}")
def get_translations_endpoint(lang: str):
    """
    Endpoint para obter traduções.
    """
    cache_key = f"translations:{lang}"
    try:
        # Verificar se temos Redis disponível
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached.decode('utf-8'))
            
        # Obter traduções diretamente do arquivo
        t = get_translations(lang)
        
        # Armazenar em cache se Redis estiver disponível
        if redis_client:
            redis_client.setex(cache_key, 3600, json.dumps(t))
            
        return t
    except Exception as e:
        logger.error(f"Erro no endpoint de tradução: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

app.include_router(router)
