from celery import Celery

# Configure Celery
app = Celery(
    "eto_app",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=[
        "src.data_download",
        "src.data_fusion",
        "src.data_preprocessing",
        "api.openmeteo",
        "api.nasapower",
    ]
)

# Configure Celery settings
app.conf.update(
    task_serializer="pickle",
    accept_content=["pickle", "json"],
    result_serializer="pickle",
    task_track_started=True,
    task_time_limit=3600,  # 1 hour timeout
    task_soft_time_limit=3300,  # 55 minutes soft timeout
    broker_connection_retry_on_startup=True,
)