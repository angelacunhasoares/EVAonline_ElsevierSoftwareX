"""
Configuração do Celery para tarefas assíncronas do EVAonline.
Centraliza todas as configurações do Celery para a aplicação.
"""
from celery import Celery
from kombu import Queue
from config.settings.app_settings import get_settings

settings = get_settings()

celery_app = Celery(
    "evaonline",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configurações principais
celery_app.conf.update(
    # Serialização
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="America/Sao_Paulo",
    enable_utc=True,
    
    # Rotas e filas
    task_default_queue="general",
    task_routes={
        "src.eto_calculator.*": {"queue": "eto_processing"},
        "src.data_download.*": {"queue": "data_download"},
        "src.data_fusion.*": {"queue": "data_processing"},
        "api.openmeteo.*": {"queue": "elevation"},
        "utils.data_utils.*": {"queue": "general"},
    },
    task_queues=(
        Queue("general"),
        Queue("eto_processing"),
        Queue("data_download"),
        Queue("data_processing"),
        Queue("elevation"),
    ),
)

# Configuração de tarefas periódicas
celery_app.conf.beat_schedule = {
    "cleanup-expired-data": {
        "task": "backend.infrastructure.cache.tasks.cleanup_expired_data",
        "schedule": 86400.0,  # 24 horas
    },
}

# Descoberta automática de tarefas
celery_app.autodiscover_tasks([
    "backend.infrastructure.cache.tasks",
    "src.eto_calculator",
    "src.data_download",
    "src.data_fusion",
    "api.openmeteo",
    "utils.data_utils"
])
