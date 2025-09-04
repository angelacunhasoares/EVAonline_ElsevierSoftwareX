#!/bin/bash

# Script para iniciar apenas os serviços de monitoramento
echo "Iniciando serviços de monitoramento (Prometheus + Grafana)..."

# Criar diretórios necessários se não existirem
mkdir -p docker/monitoring/grafana/provisioning/datasources
mkdir -p docker/monitoring/grafana/provisioning/dashboards
mkdir -p docker/monitoring/grafana/dashboards

# Iniciar apenas Prometheus e Grafana
docker-compose up -d prometheus grafana

echo "Serviços iniciados!"
echo ""
echo "Acesse o Grafana em: http://localhost:3000"
echo "Credenciais:"
echo "  Usuário: admin"
echo "  Senha: admin"
echo ""
echo "Acesse o Prometheus em: http://localhost:9090"
