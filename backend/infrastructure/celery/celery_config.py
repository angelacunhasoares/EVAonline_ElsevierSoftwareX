"""
Configuração do Celery para tarefas assíncronas do EVAonline.
Centraliza todas as configurações do Celery para a aplicação.
"""
import json
from datetime import datetime

from celery import Celery
from celery.schedules import crontab
from kombu import Queue
from redis import Redis

from backend.api.middleware.prometheus_metrics import (CELERY_TASK_DURATION,
                                                       CELERY_TASKS_TOTAL)
from config.settings.app_settings import get_settings

# Carregar configurações
settings = get_settings()

# Inicializar Celery
celery_app = Celery(
    "evaonline",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Métricas Prometheus
# As métricas são importadas do main.py para evitar duplicação

# Classe base para tarefas com monitoramento e progresso
class MonitoredProgressTask(celery_app.Task):
    def publish_progress(self, task_id, progress, status="PROGRESS"):
        """Publica progresso no canal Redis para WebSocket."""
        try:
            redis_client = Redis.from_url(
                settings.CELERY_BROKER_URL,
                decode_responses=True
            )
            redis_client.publish(
                f"task_status:{task_id}",
                json.dumps({
                    "status": status,
                    "info": progress,
                    "timestamp": datetime.now().isoformat()
                })
            )
            redis_client.close()
        except Exception as e:
            # Não bloqueia a task se falhar publicação de progresso
            import logging
            logging.warning(f"Falha ao publicar progresso: {e}")

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
        # REMOVIDO: backend.utils.data_utils.* (não contém tasks Celery)
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
    # Limpeza de cache antigo (02:00 BRT)
    "cleanup-old-climate-cache": {
        "task": "climate.cleanup_old_cache",
        "schedule": crontab(hour=2, minute=0),
    },
    # Pre-fetch cidades mundiais populares (03:00 BRT)
    "prefetch-nasa-popular-cities": {
        "task": "climate.prefetch_nasa_popular_cities",
        "schedule": crontab(hour=3, minute=0),
    },
    # Atualização MATOPIBA - 4x por dia (00h, 06h, 12h, 18h BRT)
    "update-matopiba-forecasts-00h": {
        "task": "update_matopiba_forecasts",
        "schedule": crontab(hour=0, minute=0),  # 00:00 BRT
        "options": {"queue": "eto_processing"},
    },
    "update-matopiba-forecasts-06h": {
        "task": "update_matopiba_forecasts",
        "schedule": crontab(hour=6, minute=0),  # 06:00 BRT
        "options": {"queue": "eto_processing"},
    },
    "update-matopiba-forecasts-12h": {
        "task": "update_matopiba_forecasts",
        "schedule": crontab(hour=12, minute=0),  # 12:00 BRT
        "options": {"queue": "eto_processing"},
    },
    "update-matopiba-forecasts-18h": {
        "task": "update_matopiba_forecasts",
        "schedule": crontab(hour=18, minute=0),  # 18:00 BRT
        "options": {"queue": "eto_processing"},
    },
    # Warm-up cache MATOPIBA (04:00 BRT) - DEPRECATED: usar update-matopiba-forecasts
    # "warm-cache-matopiba": {
    #     "task": "climate.warm_cache_matopiba",
    #     "schedule": crontab(hour=4, minute=0),
    # },
    # Estatísticas de cache (a cada hora)
    "generate-cache-stats": {
        "task": "climate.generate_cache_stats",
        "schedule": crontab(minute=0),  # Todo início de hora
    },
    # Tasks legadas
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
    "backend.infrastructure.cache.climate_tasks",
    "backend.infrastructure.celery.tasks",  # 🆕 MATOPIBA tasks
    "backend.core.eto_calculation",
    "backend.core.data_processing.data_download",
    "backend.core.data_processing.data_fusion",
    "backend.api.services.openmeteo",
    # "backend.utils.data_utils"  # REMOVIDO: utils não tem tasks Celery (módulo compartilhado na raiz)
])
