@echo off
echo 🔍 Teste de Conectividade Redis para VS Code
echo.

echo 1. Verificando se o Redis esta rodando...
docker-compose ps redis | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo ✅ Redis container esta rodando
) else (
    echo ❌ Redis container NAO esta rodando
    echo Execute: docker-compose up -d redis
    goto :end
)

echo.
echo 2. Testando conectividade na porta 6379...
powershell -Command "Test-NetConnection -ComputerName localhost -Port 6379 -InformationLevel Quiet" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Porta 6379 esta acessivel
) else (
    echo ❌ Porta 6379 NAO esta acessivel
)

echo.
echo 3. Testando autenticacao Redis...
docker exec evaonline-redis redis-cli -a evaonline ping 2>nul | findstr "PONG" >nul
if %errorlevel% equ 0 (
    echo ✅ Autenticacao Redis funcionando
) else (
    echo ❌ Falha na autenticacao Redis
)

echo.
echo 4. Informacoes do servidor Redis:
docker exec evaonline-redis redis-cli -a evaonline info server 2>nul | findstr "redis_version"

echo.
echo 📋 Proximos passos para VS Code:
echo 1. Abra a extensao Redis (icone do Redis na barra lateral)
echo 2. Clique no botao + para adicionar conexao
echo 3. Configure:
echo    - Name: EVAonline Redis (Docker)
echo    - Host: localhost
echo    - Port: 6379
echo    - Password: evaonline
echo    - Username: (deixe vazio)
echo 4. Clique em Test Connection
echo 5. Clique em Save

echo.
echo 🔧 Se ainda nao funcionar:
echo - Verifique se a extensao esta atualizada
echo - Tente desabilitar e reabilitar a extensao
echo - Recarregue a janela do VS Code

:end
echo.
pause
