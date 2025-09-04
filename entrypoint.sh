#!/bin/bash

# Script de entrada para o container EVAonline
# Este script gerencia o startup da aplicação baseado na variável SERVICE

set -e

# Função para aguardar serviços
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    echo "Aguardando $service_name em $host:$port..."

    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "$service_name está disponível!"
            return 0
        fi

        echo "Tentativa $attempt/$max_attempts: $service_name ainda não está disponível..."
        sleep 2
        ((attempt++))
    done

    echo "Erro: $service_name não ficou disponível após $max_attempts tentativas"
    return 1
}

# Configurar timezone
export TZ=${TZ:-America/Sao_Paulo}

# Criar diretórios necessários
mkdir -p /app/logs /app/data /app/temp

# Aguardar dependências
case "${SERVICE:-all}" in
    "api")
        echo "Iniciando serviço API..."
        wait_for_service "${POSTGRES_HOST:-postgres}" "${POSTGRES_PORT:-5432}" "PostgreSQL"
        wait_for_service "${REDIS_HOST:-redis}" "6379" "Redis"

        # Executar migrações do banco de dados se necessário
        echo "Verificando migrações do banco de dados..."
        python -c "from database.connection import get_db; db = next(get_db()); print('Conexão com banco estabelecida')" || echo "Aviso: Não foi possível verificar conexão com banco"

        # Iniciar FastAPI com Uvicorn
        echo "Iniciando FastAPI..."
        exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
        ;;

    "worker")
        echo "Iniciando worker Celery..."
        wait_for_service "${REDIS_HOST:-redis}" "6379" "Redis"

        # Iniciar worker Celery
        echo "Iniciando Celery Worker..."
        exec celery -A backend.celery_config worker --loglevel=info --concurrency=2
        ;;

    "beat")
        echo "Iniciando Celery Beat..."
        wait_for_service "${REDIS_HOST:-redis}" "6379" "Redis"

        # Iniciar Celery Beat
        echo "Iniciando Celery Beat..."
        exec celery -A backend.celery_config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
        ;;

    "flower")
        echo "Iniciando Flower..."
        wait_for_service "${REDIS_HOST:-redis}" "6379" "Redis"

        # Iniciar Flower
        echo "Iniciando Flower..."
        exec celery -A backend.celery_config flower --address=0.0.0.0 --port=5555
        ;;

    "all")
        echo "Iniciando todos os serviços..."

        # Aguardar dependências
        wait_for_service "${POSTGRES_HOST:-postgres}" "${POSTGRES_PORT:-5432}" "PostgreSQL"
        wait_for_service "${REDIS_HOST:-redis}" "6379" "Redis"

        # Executar migrações do banco de dados
        echo "Verificando migrações do banco de dados..."
        python -c "from database.connection import get_db; db = next(get_db()); print('Conexão com banco estabelecida')" || echo "Aviso: Não foi possível verificar conexão com banco"

        # Iniciar FastAPI em background
        echo "Iniciando FastAPI..."
        uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4 &

        # Aguardar um pouco para FastAPI iniciar
        sleep 5

        # Iniciar worker Celery em background
        echo "Iniciando Celery Worker..."
        celery -A backend.celery_config worker --loglevel=info --concurrency=2 &

        # Aguardar um pouco para worker iniciar
        sleep 3

        # Iniciar Celery Beat em background
        echo "Iniciando Celery Beat..."
        celery -A backend.celery_config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler &

        # Aguardar um pouco para beat iniciar
        sleep 3

        # Iniciar Flower em background
        echo "Iniciando Flower..."
        celery -A backend.celery_config flower --address=0.0.0.0 --port=5555 &

        # Manter container rodando
        echo "Todos os serviços iniciados. Container mantendo-se ativo..."
        wait
        ;;

    *)
        echo "Erro: Serviço '${SERVICE}' não reconhecido."
        echo "Serviços disponíveis: api, worker, beat, flower, all"
        exit 1
        ;;
esac
