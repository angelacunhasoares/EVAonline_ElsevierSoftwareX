"""
Inicializa e configura o banco de dados com scripts.
"""
from database.connection import Base, engine
from database.scripts import create_tables

# Módulo de inicialização para importação no app principal

def init_db():
    """
    Inicializa o banco de dados e cria as tabelas.
    """
    create_tables()
