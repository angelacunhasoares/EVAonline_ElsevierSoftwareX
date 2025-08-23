# celery_config.py
# Configuração do Celery para EVAonline

from celery import Celery
from kombu import Queue
import os

# Configuração do Redis como broker
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Criar instância do Celery
app = Celery('eva_online')

# Configurações
app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_routes={
        'src.eto_calculator.*': {'queue': 'eto_processing'},
        'src.data_download.*': {'queue': 'data_download'},
        'src.data_fusion.*': {'queue': 'data_processing'},
        'api.openmeteo.*': {'queue': 'elevation'},
        'utils.data_utils.*': {'queue': 'general'},
    },
    task_default_queue='general',
    task_queues=(
        Queue('general'),
        Queue('eto_processing'),
        Queue('data_download'),
        Queue('data_processing'),
        Queue('elevation'),
    ),
)