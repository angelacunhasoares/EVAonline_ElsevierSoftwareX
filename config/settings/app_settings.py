"""
Configurações gerais da aplicação.
Contém configurações compartilhadas entre FastAPI e Dash.
"""
import os
from functools import lru_cache
from typing import Any, Dict

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Carrega variáveis de ambiente
load_dotenv()


class Settings(BaseSettings):
    # Configurações gerais
    PROJECT_NAME: str = "EVAonline"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Configurações FastAPI
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # Configurações Dash
    DASH_URL_BASE_PATHNAME: str = "/"
    DASH_ROUTES: dict = {
        "home": "/",
        "eto_calculator": "/eto",
        "about": "/about",
        "documentation": "/documentation"
    }
    # Caminho relativo ao diretório do app.py (frontend/app.py)
    DASH_ASSETS_FOLDER: str = "assets"  # frontend/assets/
    
    # Configurações do Banco de Dados
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "127.0.0.1")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "evaonline")
    SQLALCHEMY_DATABASE_URI: str = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}"
    )
    
    # Configurações Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "evaonline")
    REDIS_URL: str = (
        f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    )
    
    # Configurações Celery
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL
    
    # Configurações de Cache
    CACHE_TTL: int = 60 * 60 * 24  # 24 horas
    
    class Config:
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """
    Retorna as configurações da aplicação.
    Usa cache para evitar múltiplas leituras do arquivo .env
    """
    return Settings()
