"""
Aplicação FastAPI principal para o EVAonline.
Gerencia todos os endpoints de API REST e WebSocket.
"""
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge

from api.services.database import get_db
from backend.api.websocket.websocket_service import router as websocket_router
from backend.api.routes.data_service import router as api_router

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
    "Number of active API requests",
    ["method", "endpoint"]
)

# Aplicação FastAPI
app = FastAPI(
    title="EVAonline API",
    description="API para acesso a dados de evapotranspiração de referência (ETo)",
    version="1.0.0",
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, deve ser mais restritivo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Métricas Prometheus
Instrumentator().instrument(app).expose(app)

# Rotas WebSocket e REST
app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
app.include_router(api_router)

@app.get("/", tags=["Raiz"])
async def root():
    """Endpoint raiz da API."""
    return {
        "mensagem": "EVAonline API - Bem-vindo!",
        "documentacao": "/docs",
        "metricas": "/metrics"
    }

@app.get("/health", tags=["Saúde"])
async def health(db=Depends(get_db)):
    """Verifica a saúde da API e do banco de dados."""
    try:
        # Verifica conexão com o banco
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Erro de saúde: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Serviço indisponível: {str(e)}"
        )
