"""
Configuração das rotas da API.
Organiza todas as rotas da aplicação por funcionalidade.
"""
from fastapi import APIRouter

from backend.api.routes.about_routes import about_router
from backend.api.routes.eto_routes import eto_router
from backend.api.routes.matopiba import matopiba_router
from backend.api.routes.system_routes import router as system_router

# Criar router principal
api_router = APIRouter()

# Incluir rotas específicas
api_router.include_router(eto_router)
api_router.include_router(about_router)
api_router.include_router(system_router)
api_router.include_router(matopiba_router)


