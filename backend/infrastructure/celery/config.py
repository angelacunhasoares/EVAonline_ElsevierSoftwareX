"""
Configuração do Celery para tarefas assíncronas.
"""
from celery import Celery
from config.settings.app_settings import get_settings

settings = get_settings()

celery_app = Celery(
    "evaonline",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configurações do Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
)

# Configuração de tarefas periódicas
celery_app.conf.beat_schedule = {
    "cleanup-expired-data": {
        "task": "backend.infrastructure.cache.tasks.cleanup_expired_data",
        "schedule": 86400.0,  # 24 horas
    },
}

# Descoberta automática de tarefas
celery_app.autodiscover_tasks(
    ["backend.infrastructure.cache.tasks"]
)
