"""
Script para criar tabelas no PostgreSQL.
"""
import logging
import sys

from ..connection import Base, engine
from ..models import EToResults

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_tables():
    """
    Cria todas as tabelas definidas nos modelos.
    """
    try:
        logger.info("Criando tabelas no PostgreSQL...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Executar como script
    create_tables()
