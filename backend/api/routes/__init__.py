"""
Configuração das rotas da API.
Organiza todas as rotas da aplicação por funcionalidade.
"""
from fastapi import APIRouter
from api.routes.eto_routes import router as eto_router
from api.routes.about_routes import router as about_router
from api.routes.data_service import router as data_router

# Criar router principal
api_router = APIRouter()

# Incluir rotas específicas
api_router.include_router(
    eto_router,
    prefix="/eto",
    tags=["evapotranspiration"]
)

api_router.include_router(
    about_router,
    prefix="/about",
    tags=["about"]
)

api_router.include_router(
    data_router,
    prefix="/data",
    tags=["data"]
)ção das rotas da API.
"""
from fastapi import APIRouter
from api.routes.data_service import router as data_router

# Criar router principal
api_router = APIRouter()

# Incluir rotas específicas
api_router.include_router(
    data_router,
    prefix="/data",
    tags=["data"]
)
