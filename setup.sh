#!/bin/bash
set -e

echo "Iniciando setup do ambiente EVA Online..."

# Instalar dependências comuns do sistema
echo "Instalando dependências do sistema..."
apt-get update
apt-get install -y locales build-essential curl
rm -rf /var/lib/apt/lists/*

# Configurar localidade
echo "Configurando localidade para pt_BR.UTF-8..."
echo "pt_BR.UTF-8 UTF-8" > /etc/locale.gen
locale-gen pt_BR.UTF-8
update-locale LANG=pt_BR.UTF-8

# Criar diretórios necessários
echo "Criando diretórios necessários..."
mkdir -p /app/logs /app/data /app/temp

# Instalar todas as dependências Python
echo "Instalando dependências Python..."
pip install --no-cache-dir -r requirements.txt

# Configurações específicas baseadas no tipo de serviço
case "${SERVICE}" in
    "api")
        echo "Configurando serviço API..."
        pip install --no-cache-dir uvicorn[standard] gunicorn prometheus_client
        ;;
    "web")
        echo "Configurando serviço Web..."
        pip install --no-cache-dir gunicorn prometheus_client
        ;;
    "celery")
        echo "Configurando serviço Celery..."
        pip install --no-cache-dir prometheus_client
        ;;
    *)
        echo "Configurando todos os serviços..."
        pip install --no-cache-dir uvicorn[standard] gunicorn prometheus_client
        ;;
esac

# Configurar permissões
echo "Configurando permissões..."
chmod -R 755 /app/logs /app/data /app/temp

echo "Setup concluído com sucesso!"