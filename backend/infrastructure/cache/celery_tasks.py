# backend/infrastructure/cache/celery_tasks.py
from celery import shared_task
from loguru import logger
from backend.core.cache.cache_manager import CacheManager
from api.services.database import SessionLocal
from utils.redis_config import redis_client
from backend.api.main import CELERY_TASKS_TOTAL, CELERY_TASK_DURATION
from redis.asyncio import Redis
import time

REDIS_URL = "redis://redis:6379/0"


@shared_task(name="backend.infrastructure.cache.celery_tasks.cleanup_expired_data")
async def cleanup_expired_data():
    start_time = time.time()
    try:
        db = SessionLocal()
        cache_manager = CacheManager(redis_client, db)
        await cache_manager.cleanup_expired_data()
        logger.info("Limpeza de dados expirados concluída com sucesso")
        CELERY_TASKS_TOTAL.labels(task_name="cleanup_expired_data", status="SUCCESS").inc()
    except Exception as e:
        logger.error(f"Erro na limpeza de dados: {str(e)}")
        CELERY_TASKS_TOTAL.labels(task_name="cleanup_expired_data", status="FAILURE").inc()
        raise
    finally:
        db.close()
        CELERY_TASK_DURATION.labels(task_name="cleanup_expired_data").observe(time.time() - start_time)


@shared_task(name="backend.infrastructure.cache.celery_tasks.update_popular_ranking")
async def update_popular_ranking():
    start_time = time.time()
    try:
        redis_client = Redis.from_url(REDIS_URL)
        keys = await redis_client.keys("acessos:*")
        for key in keys:
            acessos = int(await redis_client.get(key) or 0)
            await redis_client.zadd("ranking_acessos", {key.decode(): acessos})
        top_keys = await redis_client.zrange("ranking_acessos", 0, 9, desc=True)
        logger.info(f"Chaves mais acessadas: {top_keys}")
        CELERY_TASKS_TOTAL.labels(task_name="update_popular_ranking", status="SUCCESS").inc()
    except Exception as e:
        logger.error(f"Erro ao atualizar ranking: {str(e)}")
        CELERY_TASKS_TOTAL.labels(task_name="update_popular_ranking", status="FAILURE").inc()
        raise
    finally:
        CELERY_TASK_DURATION.labels(task_name="update_popular_ranking").observe(time.time() - start_time)