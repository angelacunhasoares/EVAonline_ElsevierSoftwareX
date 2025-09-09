"""
Inicializa e configura o banco de dados.
"""
from .connection import Base, engine, get_db_context
from .session_database import get_db

# Módulo de inicialização para importação no app principal

def init_db():
    """
    Inicializa o banco de dados e cria as tabelas.
    """
    try:
        from .models import EToResults
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        raise
