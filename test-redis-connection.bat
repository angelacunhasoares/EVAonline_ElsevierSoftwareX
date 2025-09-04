@echo off
REM Script para testar conexão Redis no Windows

echo 🔍 Testando conexão com Redis...
echo.

REM Teste básico de conectividade
echo 1. Teste de conectividade (porta 6379):
powershell -Command "Test-NetConnection -ComputerName localhost -Port 6379 -InformationLevel Quiet" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Porta 6379 está aberta
) else (
    echo ❌ Porta 6379 não está acessível
)

echo.
echo 2. Teste de autenticação Redis:
docker exec evaonline-redis redis-cli -a evaonline ping 2>nul | findstr "PONG" >nul
if %errorlevel% equ 0 (
    echo ✅ Autenticação Redis funcionando
) else (
    echo ❌ Falha na autenticação Redis
)

echo.
echo 3. Informações do servidor Redis:
docker exec evaonline-redis redis-cli -a evaonline info server 2>nul | findstr /C:"redis_version" /C:"tcp_port" /C:"uptime_in_days"

echo.
echo 4. Chaves armazenadas:
docker exec evaonline-redis redis-cli -a evaonline dbsize 2>nul

echo.
echo 📋 Instruções para VS Code:
echo - Abra Command Palette (Ctrl+Shift+P)
echo - Digite: 'Redis: Connect'
echo - Selecione: 'EVAonline Redis (Docker)'
echo - A conexão deve funcionar automaticamente
echo.
pause
