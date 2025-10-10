"""
Script para iniciar apenas a API FastAPI sem o Dash frontend.
Útil para testar os endpoints da API isoladamente.
"""
import logging
import sys
from pathlib import Path

# Adicionar projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from backend.api.middleware.prometheus import PrometheusMiddleware
from backend.api.routes import api_router
from backend.api.websocket.websocket_service import router as websocket_router
from config.settings.app_settings import get_settings

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger(__name__)

# Carregar configurações
settings = get_settings()

def create_api_only() -> FastAPI:
    """Cria aplicação FastAPI apenas com API (sem Dash)."""
    app = FastAPI(
        title=f"{settings.PROJECT_NAME} - API Only",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Permitir todas as origens para testes
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Adicionar middleware Prometheus
    app.add_middleware(PrometheusMiddleware)

    # Montar rotas
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.include_router(websocket_router)

    # Configurar métricas Prometheus
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    logger.info("✅ API FastAPI criada (sem Dash frontend)")
    logger.info(f"📚 Documentação: http://localhost:8000{settings.API_V1_PREFIX}/docs")
    logger.info(f"🔗 MATOPIBA: http://localhost:8000{settings.API_V1_PREFIX}/matopiba/metadata")
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    app = create_api_only()
    
    logger.info("🚀 Iniciando servidor Uvicorn...")
    logger.info("📍 URL: http://0.0.0.0:8000")
    logger.info("📍 MATOPIBA Metadata: http://localhost:8000/api/v1/matopiba/metadata")
    logger.info("📍 MATOPIBA Forecasts: http://localhost:8000/api/v1/matopiba/forecasts")
    logger.info("⏹️  Pressione CTRL+C para parar")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
