"""
Tarefas Celery para gerenciamento de cache e limpeza de dados.
"""
from celery import shared_task
from celery.schedules import crontab
from loguru import logger
from backend.core.cache.cache_manager import CacheManager
from api.services.database import SessionLocal
from utils.redis_config import redis_client


@shared_task(name="tasks.cleanup_expired_data")
def cleanup_expired_data():
    """
    Tarefa para limpar dados ETo expirados do PostgreSQL.
    Executada diariamente às 00:00.
    """
    try:
        db = SessionLocal()
        cache_manager = CacheManager(redis_client, db)
        await cache_manager.cleanup_expired_data()
        logger.info("Limpeza de dados expirados concluída com sucesso")
    except Exception as e:
        logger.error(f"Erro na limpeza de dados: {str(e)}")
        raise
    finally:
        db.close()


# Configuração do agendamento da tarefa
CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-data': {
        'task': 'tasks.cleanup_expired_data',
        'schedule': crontab(hour=0, minute=0)  # Execute às 00:00
    }
}
