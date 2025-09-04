@echo off
REM Script para iniciar apenas os serviços de monitoramento no Windows

echo Iniciando serviços de monitoramento (Prometheus + Grafana)...

REM Criar diretórios necessários se não existirem
if not exist "docker\monitoring\grafana\provisioning\datasources" mkdir "docker\monitoring\grafana\provisioning\datasources"
if not exist "docker\monitoring\grafana\provisioning\dashboards" mkdir "docker\monitoring\grafana\provisioning\dashboards"
if not exist "docker\monitoring\grafana\dashboards" mkdir "docker\monitoring\grafana\dashboards"

REM Iniciar apenas Prometheus e Grafana
docker-compose up -d prometheus grafana

echo.
echo Serviços iniciados!
echo.
echo Acesse o Grafana em: http://localhost:3000
echo Credenciais:
echo   Usuário: admin
echo   Senha: admin
echo.
echo Acesse o Prometheus em: http://localhost:9090
echo.
pause
