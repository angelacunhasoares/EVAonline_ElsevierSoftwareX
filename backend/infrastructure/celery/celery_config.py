"""
Configuração do Celery para tarefas assíncronas do EVAonline.
Centraliza todas as configurações do Celery para a aplicação.
"""
from celery import Celery
from kombu import Queue
from celery.schedules import crontab
from config.settings.app_settings import get_settings
from prometheus_client import Counter, Histogram
from redis.asyncio import Redis
import json
from datetime import datetime

# Carregar configurações
settings = get_settings()

# Inicializar Celery
celery_app = Celery(
    "evaonline",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Métricas Prometheus
CELERY_TASKS_TOTAL = Counter(
    "celery_tasks_total", 
    "Total de tarefas executadas", 
    ["task_name", "status"]
)
CELERY_TASK_DURATION = Histogram(
    "celery_task_duration_seconds", 
    "Duração de tarefas Celery", 
    ["task_name"]
)

# Classe base para tarefas com monitoramento e progresso
class MonitoredProgressTask(celery_app.Task):
    async def publish_progress(self, task_id, progress, status="PROGRESS"):
        """Publica progresso no canal Redis para WebSocket."""
        redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
        await redis_client.publish(f"task_status:{task_id}", json.dumps({
            "status": status,
            "info": progress,
            "timestamp": datetime.now().isoformat()
        }))
        await redis_client.close()

    def __call__(self, *args, **kwargs):
        """Rastreia duração e status da tarefa para Prometheus."""
        import time
        start_time = time.time()
        try:
            result = super().__call__(*args, **kwargs)
            CELERY_TASKS_TOTAL.labels(task_name=self.name, status="SUCCESS").inc()
            return result
        except Exception as e:
            CELERY_TASKS_TOTAL.labels(task_name=self.name, status="FAILURE").inc()
            raise
        finally:
            CELERY_TASK_DURATION.labels(task_name=self.name).observe(time.time() - start_time)

# Definir classe base para todas as tarefas
celery_app.Task = MonitoredProgressTask

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
        "backend.core.eto_calculation.*": {"queue": "eto_processing"},
        "backend.core.data_processing.data_download.*": {"queue": "data_download"},
        "backend.core.data_processing.data_fusion.*": {"queue": "data_processing"},
        "backend.api.services.openmeteo.*": {"queue": "elevation"},
        "backend.utils.data_utils.*": {"queue": "general"},
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
        "task": "backend.infrastructure.cache.celery_tasks.cleanup_expired_data",
        "schedule": crontab(hour=0, minute=0),  # 00:00 diariamente
    },
    "update-popular-ranking": {
        "task": "backend.infrastructure.cache.celery_tasks.update_popular_ranking",
        "schedule": crontab(minute="*/10"),  # A cada 10 minutos
    },
}

# Descoberta automática de tarefas
celery_app.autodiscover_tasks([
    "backend.infrastructure.cache.celery_tasks",
    "backend.core.eto_calculation",
    "backend.core.data_processing.data_download",
    "backend.core.data_processing.data_fusion",
    "backend.api.services.openmeteo",
    "backend.utils.data_utils"
])