"""
Sistema de cache da aplicação.
"""
from backend.infrastructure.cache.manager import CacheManager
from backend.infrastructure.cache.tasks import cleanup_expired_data

__all__ = ["CacheManager", "cleanup_expired_data"]
