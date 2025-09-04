#!/bin/sh

# Aguardar serviços ficarem prontos
echo "Aguardando PostgreSQL..."
while ! nc -z db 5432; do
    sleep 1
done
echo "✅ PostgreSQL está pronto!"

echo "Aguardando Redis..."
while ! nc -z redis 6379; do
    sleep 1
done
echo "✅ Redis está pronto!"

# Executar migrações do banco de dados (se houver)
echo "Verificando migrações do banco de dados..."
cd /app && python -c "
try:
    from backend.database.connection import get_db
    from backend.database.models import Base
    from sqlalchemy import create_engine
    import os

    # Criar engine com URL do banco
    db_url = os.getenv('DATABASE_URL', 'postgresql://evaonline:evaonline@db:5432/evaonline')
    engine = create_engine(db_url)

    # Criar tabelas se não existirem
    Base.metadata.create_all(bind=engine)
    print('✅ Tabelas do banco de dados verificadas/criadas')
except Exception as e:
    print(f'⚠️  Aviso ao verificar tabelas: {e}')
"

# Iniciar a aplicação FastAPI
echo "🚀 Iniciando aplicação FastAPI..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
