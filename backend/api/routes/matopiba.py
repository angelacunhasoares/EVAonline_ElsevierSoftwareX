"""
Rotas API para previsões MATOPIBA.

Este módulo implementa:
- GET /api/matopiba/forecasts: Retorna previsões completas do Redis
- GET /api/matopiba/metadata: Retorna apenas metadata (status, próxima atualização)
- POST /api/matopiba/refresh: Força atualização manual (admin apenas)

Autor: EVAonline Team
Data: 2025-10-09
"""

import json
import os
import pickle
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from redis import Redis
from redis.exceptions import RedisError

# Configuração
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")  # Vazio por padrão para dev local
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")

# Constrói URL com ou sem senha
if REDIS_PASSWORD:
    REDIS_URL = f"redis://default:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

REDIS_KEY_FORECASTS = "matopiba:forecasts:today_tomorrow"
REDIS_KEY_METADATA = "matopiba:metadata"

# Router para endpoints MATOPIBA
matopiba_router = APIRouter(
    prefix="/api/matopiba",
    tags=["MATOPIBA Forecasts"]
)


def get_redis_client() -> Redis:
    """
    Cria conexão Redis.
    
    Returns:
        Cliente Redis conectado
    
    Raises:
        HTTPException: Se conexão falhar
    """
    try:
        client = Redis.from_url(REDIS_URL, decode_responses=False)
        client.ping()
        return client
    except RedisError as e:
        logger.error("Erro ao conectar Redis: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de cache indisponível. Tente novamente em instantes."
        )


@matopiba_router.get("/forecasts")
async def get_matopiba_forecasts() -> Dict:
    """
    Retorna previsões meteorológicas completas para MATOPIBA.
    
    Dados incluem:
    - forecasts: Dados de 337 cidades × 2 dias (hoje + amanhã)
    - validation: Métricas de validação (R², RMSE, Bias, status)
    - metadata: Informações de atualização e próxima execução
    
    Returns:
        Dict com estrutura:
        {
            "forecasts": {
                "city_code": {
                    "city_info": {...},
                    "forecast": {
                        "2025-10-09": {
                            "T2M_MAX": 35.2,
                            "T2M_MIN": 22.1,
                            "ETo_EVAonline": 5.23,
                            "ETo_OpenMeteo": 5.18,
                            "PRECTOTCORR": 0.0,
                            ...
                        }
                    }
                },
                ...
            },
            "validation": {
                "r2": 0.89,
                "rmse": 0.45,
                "bias": 0.05,
                "mae": 0.38,
                "n_samples": 674,
                "status": "EXCELENTE"
            },
            "metadata": {
                "updated_at": "2025-10-09T00:00:00",
                "next_update": "2025-10-09T06:00:00",
                "n_cities": 337,
                "success_rate": 100.0,
                "version": "1.0.0"
            }
        }
    
    Raises:
        HTTPException 503: Se cache estiver vazio ou expirado
        HTTPException 500: Se houver erro ao processar dados
    """
    try:
        logger.info("GET /api/matopiba/forecasts")
        
        redis_client = get_redis_client()
        
        # Verificar se cache existe
        if not redis_client.exists(REDIS_KEY_FORECASTS):
            logger.warning("Cache MATOPIBA vazio")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Previsões ainda não disponíveis. "
                    "Aguarde a primeira atualização (executada a cada 6h: 00h, 06h, 12h, 18h)."
                )
            )
        
        # Obter dados do cache
        try:
            cache_data_raw = redis_client.get(REDIS_KEY_FORECASTS)
            cache_data = pickle.loads(cache_data_raw)
            
            # Adicionar TTL ao metadata
            ttl_seconds = redis_client.ttl(REDIS_KEY_FORECASTS)
            cache_data['metadata']['ttl_seconds'] = ttl_seconds
            cache_data['metadata']['ttl_minutes'] = round(ttl_seconds / 60, 1)
            
            logger.info(
                "✅ Cache retornado: %d cidades, TTL: %d min",
                cache_data['metadata']['n_cities'],
                ttl_seconds / 60
            )
            
            return cache_data
            
        except pickle.UnpicklingError as e:
            logger.error("Erro ao deserializar cache: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao processar dados de previsão."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro inesperado em /forecasts: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@matopiba_router.get("/metadata")
async def get_matopiba_metadata() -> Dict:
    """
    Retorna apenas metadata das previsões MATOPIBA (rápido).
    
    Útil para:
    - Verificar última atualização
    - Checar próxima atualização
    - Validar se cache está ativo
    
    Returns:
        Dict com metadata:
        {
            "status": "ACTIVE" | "EMPTY" | "ERROR",
            "updated_at": "2025-10-09T00:00:00",
            "next_update": "2025-10-09T06:00:00",
            "n_cities": 337,
            "success_rate": 100.0,
            "ttl_seconds": 21600,
            "ttl_minutes": 360.0,
            "version": "1.0.0"
        }
    """
    try:
        logger.info("GET /api/matopiba/metadata")
        
        redis_client = get_redis_client()
        
        # Verificar se cache existe
        if not redis_client.exists(REDIS_KEY_METADATA):
            return {
                "status": "EMPTY",
                "message": "Aguardando primeira atualização",
                "next_scheduled_updates": [
                    "00:00 UTC-3",
                    "06:00 UTC-3",
                    "12:00 UTC-3",
                    "18:00 UTC-3"
                ]
            }
        
        # Obter metadata
        try:
            metadata_raw = redis_client.get(REDIS_KEY_METADATA)
            metadata = json.loads(metadata_raw)
            
            # Adicionar TTL
            ttl_seconds = redis_client.ttl(REDIS_KEY_METADATA)
            metadata['ttl_seconds'] = ttl_seconds
            metadata['ttl_minutes'] = round(ttl_seconds / 60, 1)
            metadata['status'] = 'ACTIVE'
            
            logger.info("✅ Metadata retornada (TTL: %d min)", ttl_seconds / 60)
            
            return metadata
            
        except json.JSONDecodeError as e:
            logger.error("Erro ao decodificar metadata: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao processar metadata."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro inesperado em /metadata: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@matopiba_router.get("/status")
async def get_matopiba_status() -> Dict:
    """
    Verifica status do sistema MATOPIBA (health check).
    
    Returns:
        Dict com status:
        {
            "cache_status": "ACTIVE" | "EMPTY",
            "redis_status": "CONNECTED" | "DISCONNECTED",
            "last_update": "2025-10-09T00:00:00" | null,
            "next_update": "2025-10-09T06:00:00" | null
        }
    """
    try:
        logger.info("GET /api/matopiba/status")
        
        # Testar Redis
        try:
            redis_client = get_redis_client()
            redis_status = "CONNECTED"
        except HTTPException:
            return {
                "cache_status": "UNKNOWN",
                "redis_status": "DISCONNECTED",
                "last_update": None,
                "next_update": None,
                "error": "Redis indisponível"
            }
        
        # Verificar cache
        cache_exists = redis_client.exists(REDIS_KEY_FORECASTS)
        
        if not cache_exists:
            return {
                "cache_status": "EMPTY",
                "redis_status": redis_status,
                "last_update": None,
                "next_update": None,
                "message": "Aguardando primeira atualização automática"
            }
        
        # Obter metadata
        metadata_raw = redis_client.get(REDIS_KEY_METADATA)
        if metadata_raw:
            metadata = json.loads(metadata_raw)
            last_update = metadata.get('updated_at')
            next_update = metadata.get('next_update')
        else:
            last_update = None
            next_update = None
        
        return {
            "cache_status": "ACTIVE",
            "redis_status": redis_status,
            "last_update": last_update,
            "next_update": next_update,
            "ttl_minutes": round(redis_client.ttl(REDIS_KEY_FORECASTS) / 60, 1)
        }
    
    except Exception as e:
        logger.exception("Erro em /status: %s", e)
        return {
            "cache_status": "ERROR",
            "redis_status": "UNKNOWN",
            "last_update": None,
            "next_update": None,
            "error": str(e)
        }


@matopiba_router.post("/refresh")
async def force_refresh_matopiba() -> Dict:
    """
    Força atualização manual das previsões MATOPIBA.
    
    ⚠️ ATENÇÃO: Esta operação pode demorar 5-10 minutos.
    Use apenas para testes ou emergências.
    
    Returns:
        Dict com task_id para acompanhamento
    
    TODO: Implementar autenticação (admin apenas)
    """
    try:
        logger.warning("POST /api/matopiba/refresh - Atualização manual solicitada")
        
        # Importar task (lazy import para evitar circular dependency)
        from backend.infrastructure.celery.tasks.matopiba_forecast_task import \
            update_matopiba_forecasts

        # Disparar task assíncrona
        task = update_matopiba_forecasts.delay()
        
        logger.info("Task disparada: %s", task.id)
        
        return {
            "status": "ACCEPTED",
            "message": "Atualização iniciada em background",
            "task_id": task.id,
            "estimated_duration_minutes": "5-10 minutos",
            "check_status_at": f"/api/matopiba/task-status/{task.id}"
        }
    
    except Exception as e:
        logger.exception("Erro ao disparar atualização: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar atualização: {str(e)}"
        )


@matopiba_router.get("/task-status/{task_id}")
async def get_task_status(task_id: str) -> Dict:
    """
    Verifica status de uma task de atualização.
    
    Args:
        task_id: ID da task Celery
    
    Returns:
        Dict com status da task
    """
    try:
        from celery.result import AsyncResult

        from backend.infrastructure.celery.celery_config import celery_app
        
        task_result = AsyncResult(task_id, app=celery_app)
        
        return {
            "task_id": task_id,
            "status": task_result.status,
            "ready": task_result.ready(),
            "successful": task_result.successful() if task_result.ready() else None,
            "result": task_result.result if task_result.ready() else None
        }
    
    except Exception as e:
        logger.error("Erro ao verificar task: %s", e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task não encontrada: {task_id}"
        )


# Health check endpoint
@matopiba_router.get("/health")
async def health_check() -> Dict:
    """
    Health check simples para monitoramento.
    
    Returns:
        Dict com status OK
    """
    return {
        "status": "OK",
        "service": "MATOPIBA Forecasts API",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
