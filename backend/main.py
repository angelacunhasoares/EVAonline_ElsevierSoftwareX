import logging

from asgiref.wsgi import WsgiToAsgi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from backend.api.middleware.prometheus_metrics import (API_ACTIVE_REQUESTS,
                                                       API_REQUEST_DURATION,
                                                       API_REQUESTS,
                                                       CACHE_HITS,
                                                       CACHE_MISSES,
                                                       CELERY_TASK_DURATION,
                                                       CELERY_TASKS_TOTAL,
                                                       POPULAR_DATA_ACCESSES)
from backend.api.routes import api_router
from backend.api.websocket.websocket_service import router as websocket_router
from config.settings.app_settings import get_settings
from frontend.app import create_dash_app

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler("logs/api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carregar configurações
settings = get_settings()

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Adicionar middleware Prometheus
    from backend.api.middleware.prometheus import PrometheusMiddleware
    app.add_middleware(PrometheusMiddleware)

    # Montar rotas
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.include_router(websocket_router)

    # Configurar métricas Prometheus
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    return app


def mount_dash(app: FastAPI) -> FastAPI:
    dash_app = create_dash_app()
    # Converter WSGI app para ASGI app
    asgi_app = WsgiToAsgi(dash_app.server)
    app.mount(
        settings.DASH_URL_BASE_PATHNAME,
        asgi_app,
        name="dash_app"
    )
    return app


app = create_application()
app = mount_dash(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
