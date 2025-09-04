"""
Métricas globais do Prometheus para a aplicação EVAonline.
Centraliza todas as definições de métricas para evitar duplicação.
"""
from prometheus_client import Counter, Gauge, Histogram

# Métricas da API
API_REQUESTS = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status_code"]
)
API_REQUEST_DURATION = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"]
)
API_ACTIVE_REQUESTS = Gauge(
    "api_active_requests",
    "Number of currently active requests",
    ["method", "endpoint"]
)

# Métricas para cache e Celery
CACHE_HITS = Counter("redis_cache_hits", "Cache hits", ["key"])
CACHE_MISSES = Counter("redis_cache_misses", "Cache misses", ["key"])
POPULAR_DATA_ACCESSES = Counter("popular_data_accesses", "Acessos a dados populares", ["key"])
CELERY_TASK_DURATION = Histogram(
    "celery_task_duration_seconds",
    "Duração de tarefas Celery",
    ["task_name"]
)
CELERY_TASKS_TOTAL = Counter(
    "celery_tasks_total",
    "Total de tarefas executadas",
    ["task_name", "status"]
)
