import time

from celery import shared_task
from loguru import logger
from redis.asyncio import Redis

from backend.main import CELERY_TASK_DURATION, CELERY_TASKS_TOTAL
from config.settings.app_settings import get_settings

# Fallback para métricas locais se houver problema de importação
try:
    # Importar métricas globais do main.py para evitar duplicação
    from backend.api.middleware.prometheus_metrics import (
        CELERY_TASK_DURATION, CELERY_TASKS_TOTAL)
except ImportError:
    # Métricas dummy se prometheus não estiver disponível
    class DummyMetric:
        def labels(self, **kwargs):
            return self

        def inc(self):
            pass

        def observe(self, value):
            pass

    CELERY_TASKS_TOTAL = DummyMetric()
    CELERY_TASK_DURATION = DummyMetric()

# Carregar configurações
settings = get_settings()
REDIS_URL = settings.REDIS_URL


@shared_task(name="backend.infrastructure.cache.celery_tasks."
             "cleanup_expired_data")
async def cleanup_expired_data():
    start_time = time.time()
    try:
        redis_client = Redis.from_url(REDIS_URL)
        expired_keys = await redis_client.keys("forecast:expired:*")
        if expired_keys:
            await redis_client.delete(*expired_keys)
            logger.info(f"Removidas {len(expired_keys)} chaves expiradas")
        
        logger.info("Limpeza de dados expirados concluída com sucesso")
        CELERY_TASKS_TOTAL.labels(
            task_name="cleanup_expired_data", status="SUCCESS"
        ).inc()
        
    except Exception as e:
        logger.error(f"Erro na limpeza de dados: {str(e)}")
        CELERY_TASKS_TOTAL.labels(
            task_name="cleanup_expired_data", status="FAILURE"
        ).inc()
        raise
    finally:
        CELERY_TASK_DURATION.labels(
            task_name="cleanup_expired_data"
        ).observe(time.time() - start_time)


@shared_task(name="backend.infrastructure.cache.celery_tasks."
             "update_popular_ranking")
async def update_popular_ranking():
    start_time = time.time()
    try:
        redis_client = Redis.from_url(REDIS_URL)
        keys = await redis_client.keys("acessos:*")
        for key in keys:
            acessos = int(await redis_client.get(key) or 0)
            await redis_client.zadd("ranking_acessos", {key.decode(): acessos})
        
        top_keys = await redis_client.zrange(
            "ranking_acessos", 0, 9, desc=True
        )
        logger.info(f"Chaves mais acessadas: {top_keys}")
        
        CELERY_TASKS_TOTAL.labels(
            task_name="update_popular_ranking", status="SUCCESS"
        ).inc()
        
    except Exception as e:
        logger.error(f"Erro ao atualizar ranking: {str(e)}")
        CELERY_TASKS_TOTAL.labels(
            task_name="update_popular_ranking", status="FAILURE"
        ).inc()
        raise
    finally:
        CELERY_TASK_DURATION.labels(
            task_name="update_popular_ranking"
        ).observe(time.time() - start_time)

