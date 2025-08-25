"""
Serviço de gerenciamento de cache que integra Redis e PostgreSQL.
Implementa estratégias de cache e persistência para dados ETo.
"""
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, Any
import redis
from sqlalchemy.orm import Session
from loguru import logger

class CacheManager:
    def __init__(
        self,
        redis_client: redis.Redis,
        db_session: Session,
        eto_expiry: int = 86400,  # 1 dia em segundos
        user_data_expiry: int = 2592000,  # 30 dias em segundos
    ):
        self.redis = redis_client
        self.db = db_session
        self.eto_expiry = eto_expiry
        self.user_data_expiry = user_data_expiry

    async def get_eto_data(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Busca dados ETo primeiro no Redis, se não encontrar, busca no PostgreSQL.
        """
        # Tenta buscar do Redis
        data = await self._get_from_redis(key)
        if data:
            logger.info(f"Cache hit para key: {key}")
            return data

        # Se não encontrou no Redis, busca no PostgreSQL
        logger.info(f"Cache miss para key: {key}, buscando no PostgreSQL")
        data = await self._get_from_postgres(key)
        if data:
            # Se encontrou no PostgreSQL, atualiza o Redis
            await self._set_in_redis(key, data, self.eto_expiry)
            return data

        return None

    async def save_eto_data(self, key: str, data: Dict[str, Any]):
        """
        Salva dados ETo no Redis e PostgreSQL.
        """
        try:
            # Salva no Redis com expiração
            await self._set_in_redis(key, data, self.eto_expiry)
            
            # Salva no PostgreSQL
            await self._save_to_postgres(key, data)
            
            logger.info(f"Dados salvos com sucesso para key: {key}")
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {str(e)}")
            raise

    async def _get_from_redis(self, key: str) -> Optional[Dict[str, Any]]:
        """Busca dados do Redis."""
        try:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Erro ao buscar do Redis: {str(e)}")
            return None

    async def _set_in_redis(self, key: str, data: Dict[str, Any], expiry: int):
        """Salva dados no Redis com expiração."""
        try:
            self.redis.setex(
                key,
                expiry,
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"Erro ao salvar no Redis: {str(e)}")
            raise

    async def _get_from_postgres(self, key: str) -> Optional[Dict[str, Any]]:
        """Busca dados do PostgreSQL."""
        try:
            result = self.db.execute(
                """
                SELECT data, created_at 
                FROM eto_results 
                WHERE key = :key
                ORDER BY created_at DESC 
                LIMIT 1
                """,
                {"key": key}
            ).first()

            if result:
                data, created_at = result
                # Verifica se os dados ainda são válidos (menos de 24h)
                if datetime.now() - created_at < timedelta(days=1):
                    return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar do PostgreSQL: {str(e)}")
            return None

    async def _save_to_postgres(self, key: str, data: Dict[str, Any]):
        """Salva dados no PostgreSQL."""
        try:
            self.db.execute(
                """
                INSERT INTO eto_results (key, data, created_at)
                VALUES (:key, :data, :created_at)
                """,
                {
                    "key": key,
                    "data": json.dumps(data),
                    "created_at": datetime.now()
                }
            )
            self.db.commit()
        except Exception as e:
            logger.error(f"Erro ao salvar no PostgreSQL: {str(e)}")
            self.db.rollback()
            raise

    async def cleanup_expired_data(self):
        """
        Remove dados expirados do PostgreSQL.
        Deve ser executado periodicamente (ex: diariamente).
        """
        try:
            self.db.execute(
                """
                DELETE FROM eto_results 
                WHERE created_at < :expiry_date
                """,
                {
                    "expiry_date": datetime.now() - timedelta(days=1)
                }
            )
            self.db.commit()
            logger.info("Limpeza de dados expirados concluída")
        except Exception as e:
            logger.error(f"Erro na limpeza de dados: {str(e)}")
            self.db.rollback()
            raise
