"""
Módulo base para configuração e conexão com o banco de dados PostgreSQL.
"""
import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configurações do PostgreSQL - usando variáveis de ambiente ou valores padrão
PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_USER = os.getenv("POSTGRES_USER", "evaonline")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "123456")
PG_DB = os.getenv("POSTGRES_DB", "evaonline")

# URL de conexão com o PostgreSQL
DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

# Criar engine SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica a conexão antes de usá-la
    pool_recycle=3600,   # Recicla conexões a cada 1 hora
    echo=False           # Define como True para ver logs SQL
)

# Criar fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos declarativos
Base = declarative_base()


@contextmanager
def get_db_context():
    """
    Context manager para sessões de banco de dados.
    Garante que a sessão seja fechada após o uso.
    
    Yields:
        Session: Uma sessão de banco de dados
    
    Exemplo:
        with get_db_context() as db:
            db.execute(...)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
