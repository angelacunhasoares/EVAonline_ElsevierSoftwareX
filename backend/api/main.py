"""
Arquivo principal da aplicação FastAPI.
Configura e inicializa a aplicação FastAPI e monta o Dash.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge

from config.settings.app_settings import get_settings
from api.routes import api_router
from api.websocket.websocket_service import router as websocket_router
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

# Métricas Prometheus
API_REQUESTS = Counter(
    "api_requests_total", 
    "Total number of API requests",
    ["method", "endpoint", "status_code"]
)

API_REQUEST_DURATION = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"]
)

API_ACTIVE_REQUESTS = Gauge(
    "api_active_requests",
    "Number of currently active requests",
    ["method", "endpoint"]
)

def create_application() -> FastAPI:
    """
    Cria e configura a aplicação FastAPI.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    )

    # Configurar middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Adicionar middleware Prometheus
    from api.middleware.prometheus import PrometheusMiddleware
    app.add_middleware(PrometheusMiddleware)

    # Montar rotas da API
    app.include_router(
        api_router,
        prefix=settings.API_V1_PREFIX
    )

    # Montar rotas WebSocket
    app.include_router(websocket_router)

    # Configurar métricas Prometheus
    Instrumentator().instrument(app).expose(app)

    return app


def mount_dash(app: FastAPI) -> FastAPI:
    """
    Monta o aplicativo Dash no FastAPI.
    """
    dash_app = create_dash_app()
    app.mount(
        settings.DASH_URL_BASE_PATHNAME,
        dash_app.server,
        name="dash_app"
    )
    return app


# Criar e configurar a aplicação
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
