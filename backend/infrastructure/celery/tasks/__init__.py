"""Celery tasks package."""

# Import all tasks to register them with Celery
from .matopiba_forecast_task import (get_matopiba_cache_status,
                                     update_matopiba_forecasts)

__all__ = [
    "update_matopiba_forecasts",
    "get_matopiba_cache_status",
]
