"""
Serviços gerais da API (saúde, métricas, etc.).
"""
from fastapi import APIRouter
from prometheus_client import Counter, generate_latest
from starlette.responses import Response

# Criar router
router = APIRouter(tags=["system"])

# Métrica do Prometheus para contar requisições
REQUESTS = Counter('evaonline_requests_total', 'Total API Requests')


@router.get("/health")
async def health_check():
    """
    Endpoint para verificação de saúde da API.
    """
    REQUESTS.inc()
    return {
        "status": "ok",
        "service": "evaonline-api",
        "version": "1.0.0"
    }


@router.get("/metrics")
async def metrics():
    """
    Endpoint para expor métricas do Prometheus.
    """
    REQUESTS.inc()
    return Response(generate_latest(), media_type="text/plain")
