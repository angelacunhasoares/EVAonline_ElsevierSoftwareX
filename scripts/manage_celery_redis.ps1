# EVAonline MATOPIBA - Script de Gerenciamento Celery + Redis
# Facilita iniciar/parar serviços e executar testes
#
# Uso:
#   .\scripts\manage_celery_redis.ps1 start-all    # Iniciar tudo
#   .\scripts\manage_celery_redis.ps1 stop-all     # Parar tudo
#   .\scripts\manage_celery_redis.ps1 test         # Testar integração
#   .\scripts\manage_celery_redis.ps1 status       # Ver status
#   .\scripts\manage_celery_redis.ps1 logs         # Ver logs
#   .\scripts\manage_celery_redis.ps1 trigger      # Executar task manualmente

param(
    [Parameter(Position=0)]
    [ValidateSet('start-all', 'stop-all', 'start-redis', 'stop-redis', 
                 'start-worker', 'stop-worker', 'start-beat', 'stop-beat',
                 'start-flower', 'stop-flower', 'test', 'status', 'logs',
                 'trigger', 'purge', 'help')]
    [string]$Command = 'help'
)

# Cores
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Cyan = "Cyan"

# Configurações
$RedisContainer = "evaonline-redis"
$RedisPort = 6379
$RedisPassword = "evaonline"
$FlowerPort = 5555

# Verificar se está na raiz do projeto
if (-not (Test-Path ".\backend\infrastructure\celery\celery_config.py")) {
    Write-Host "❌ Execute este script da raiz do projeto EVAonline" -ForegroundColor $Red
    exit 1
}

# ============================================================================
# Funções Redis
# ============================================================================

function Start-Redis {
    Write-Host "`n🔄 Iniciando Redis..." -ForegroundColor $Cyan
    
    # Verificar se já existe
    $existing = docker ps -a --filter "name=$RedisContainer" --format "{{.Names}}"
    
    if ($existing -eq $RedisContainer) {
        # Container existe, apenas iniciar
        $running = docker ps --filter "name=$RedisContainer" --format "{{.Names}}"
        if ($running -eq $RedisContainer) {
            Write-Host "✅ Redis já está rodando" -ForegroundColor $Green
        } else {
            docker start $RedisContainer | Out-Null
            Write-Host "✅ Redis iniciado" -ForegroundColor $Green
        }
    } else {
        # Criar novo container
        docker run -d `
            --name $RedisContainer `
            -p ${RedisPort}:6379 `
            -e REDIS_PASSWORD=$RedisPassword `
            --restart unless-stopped `
            redis:7-alpine redis-server --requirepass $RedisPassword | Out-Null
        
        Write-Host "✅ Redis criado e iniciado" -ForegroundColor $Green
    }
    
    # Testar conexão
    Start-Sleep -Seconds 2
    $ping = docker exec $RedisContainer redis-cli -a $RedisPassword PING 2>$null
    if ($ping -eq "PONG") {
        Write-Host "✅ Redis respondendo: PONG" -ForegroundColor $Green
    } else {
        Write-Host "⚠️  Redis não respondeu ao PING" -ForegroundColor $Yellow
    }
}

function Stop-Redis {
    Write-Host "`n🔄 Parando Redis..." -ForegroundColor $Cyan
    docker stop $RedisContainer 2>$null | Out-Null
    Write-Host "✅ Redis parado" -ForegroundColor $Green
}

# ============================================================================
# Funções Celery Worker
# ============================================================================

function Start-CeleryWorker {
    Write-Host "`n🔄 Iniciando Celery Worker..." -ForegroundColor $Cyan
    
    # Verificar se venv existe
    if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
        Write-Host "❌ Ambiente virtual não encontrado em .\.venv" -ForegroundColor $Red
        return
    }
    
    # Iniciar em nova janela PowerShell
    $scriptBlock = {
        Set-Location $using:PWD
        .\.venv\Scripts\Activate.ps1
        Write-Host "🚀 Celery Worker - Pressione Ctrl+C para parar" -ForegroundColor Green
        celery -A backend.infrastructure.celery.celery_config:celery_app worker `
            --loglevel=info `
            --pool=solo `
            --concurrency=4 `
            --hostname=worker@matopiba `
            --queues=general,eto_processing,data_download
    }
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {$scriptBlock}"
    Write-Host "✅ Celery Worker iniciado em nova janela" -ForegroundColor $Green
}

function Stop-CeleryWorker {
    Write-Host "`n🔄 Parando Celery Workers..." -ForegroundColor $Cyan
    
    # Parar processos celery worker
    $processes = Get-Process | Where-Object {$_.ProcessName -like "*celery*"}
    if ($processes) {
        $processes | Stop-Process -Force
        Write-Host "✅ Celery Workers parados" -ForegroundColor $Green
    } else {
        Write-Host "⚠️  Nenhum Celery Worker encontrado" -ForegroundColor $Yellow
    }
}

# ============================================================================
# Funções Celery Beat
# ============================================================================

function Start-CeleryBeat {
    Write-Host "`n🔄 Iniciando Celery Beat..." -ForegroundColor $Cyan
    
    if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
        Write-Host "❌ Ambiente virtual não encontrado" -ForegroundColor $Red
        return
    }
    
    $scriptBlock = {
        Set-Location $using:PWD
        .\.venv\Scripts\Activate.ps1
        Write-Host "⏰ Celery Beat - Pressione Ctrl+C para parar" -ForegroundColor Green
        celery -A backend.infrastructure.celery.celery_config:celery_app beat `
            --loglevel=info
    }
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {$scriptBlock}"
    Write-Host "✅ Celery Beat iniciado em nova janela" -ForegroundColor $Green
}

function Stop-CeleryBeat {
    Write-Host "`n🔄 Parando Celery Beat..." -ForegroundColor $Cyan
    
    $processes = Get-Process | Where-Object {$_.CommandLine -like "*celery*beat*"}
    if ($processes) {
        $processes | Stop-Process -Force
        Write-Host "✅ Celery Beat parado" -ForegroundColor $Green
    } else {
        Write-Host "⚠️  Celery Beat não encontrado" -ForegroundColor $Yellow
    }
}

# ============================================================================
# Funções Flower
# ============================================================================

function Start-Flower {
    Write-Host "`n🔄 Iniciando Flower..." -ForegroundColor $Cyan
    
    if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
        Write-Host "❌ Ambiente virtual não encontrado" -ForegroundColor $Red
        return
    }
    
    $scriptBlock = {
        Set-Location $using:PWD
        .\.venv\Scripts\Activate.ps1
        Write-Host "🌸 Flower - Interface web em http://localhost:$using:FlowerPort" -ForegroundColor Green
        celery -A backend.infrastructure.celery.celery_config:celery_app flower `
            --port=$using:FlowerPort
    }
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {$scriptBlock}"
    Write-Host "✅ Flower iniciado: http://localhost:$FlowerPort" -ForegroundColor $Green
}

function Stop-Flower {
    Write-Host "`n🔄 Parando Flower..." -ForegroundColor $Cyan
    
    $processes = Get-Process | Where-Object {$_.CommandLine -like "*flower*"}
    if ($processes) {
        $processes | Stop-Process -Force
        Write-Host "✅ Flower parado" -ForegroundColor $Green
    } else {
        Write-Host "⚠️  Flower não encontrado" -ForegroundColor $Yellow
    }
}

# ============================================================================
# Funções de Teste
# ============================================================================

function Test-Integration {
    Write-Host "`n🧪 Executando testes de integração..." -ForegroundColor $Cyan
    
    .\.venv\Scripts\Activate.ps1
    
    Write-Host "`n1️⃣  Testando conexão Redis..." -ForegroundColor $Cyan
    & .\.venv\Scripts\python.exe .\scripts\test_redis_connection.py
    
    Write-Host "`n2️⃣  Testando pipeline MATOPIBA..." -ForegroundColor $Cyan
    & .\.venv\Scripts\python.exe -m backend.tests.test_matopiba_integration
}

function Get-Status {
    Write-Host "`n📊 STATUS DOS SERVIÇOS" -ForegroundColor $Cyan
    Write-Host "="*60
    
    # Redis
    Write-Host "`n🔴 Redis:" -ForegroundColor $Yellow
    $redis = docker ps --filter "name=$RedisContainer" --format "{{.Status}}"
    if ($redis) {
        Write-Host "  ✅ Rodando: $redis" -ForegroundColor $Green
        
        # Testar PING
        $ping = docker exec $RedisContainer redis-cli -a $RedisPassword PING 2>$null
        if ($ping -eq "PONG") {
            Write-Host "  ✅ Respondendo: PONG" -ForegroundColor $Green
            
            # Estatísticas
            $dbsize = docker exec $RedisContainer redis-cli -a $RedisPassword DBSIZE 2>$null
            Write-Host "  📦 Chaves: $dbsize" -ForegroundColor $Cyan
        }
    } else {
        Write-Host "  ❌ Não está rodando" -ForegroundColor $Red
    }
    
    # Celery Worker
    Write-Host "`n⚙️  Celery Worker:" -ForegroundColor $Yellow
    $workers = Get-Process | Where-Object {$_.ProcessName -like "*celery*"} | Measure-Object
    if ($workers.Count -gt 0) {
        Write-Host "  ✅ Processos ativos: $($workers.Count)" -ForegroundColor $Green
    } else {
        Write-Host "  ❌ Não está rodando" -ForegroundColor $Red
    }
    
    # Flower
    Write-Host "`n🌸 Flower:" -ForegroundColor $Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$FlowerPort" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "  ✅ Acessível: http://localhost:$FlowerPort" -ForegroundColor $Green
    } catch {
        Write-Host "  ❌ Não está rodando" -ForegroundColor $Red
    }
    
    Write-Host "`n" + "="*60
}

function Get-Logs {
    Write-Host "`n📋 LOGS RECENTES" -ForegroundColor $Cyan
    Write-Host "="*60
    
    # Logs Redis
    Write-Host "`n🔴 Redis (últimas 20 linhas):" -ForegroundColor $Yellow
    docker logs $RedisContainer --tail 20 2>$null
    
    # Logs API
    if (Test-Path ".\logs\api.log") {
        Write-Host "`n📡 API (últimas 20 linhas):" -ForegroundColor $Yellow
        Get-Content ".\logs\api.log" -Tail 20
    }
    
    Write-Host "`n" + "="*60
}

function Invoke-TaskManually {
    Write-Host "`n🚀 Executando task update_matopiba_forecasts manualmente..." -ForegroundColor $Cyan
    
    .\.venv\Scripts\Activate.ps1
    
    & .\.venv\Scripts\python.exe -c @"
from backend.infrastructure.celery.tasks.matopiba_forecast_task import update_matopiba_forecasts
result = update_matopiba_forecasts.delay()
print(f'✅ Task enviada: {result.id}')
print('⏳ Aguarde ~60-90s para conclusão...')
print(f'💡 Acompanhe o progresso nos logs do Celery Worker')
"@
}

function Clear-Tasks {
    Write-Host "`n🗑️  Limpando tasks pendentes..." -ForegroundColor $Cyan
    
    .\.venv\Scripts\Activate.ps1
    celery -A backend.infrastructure.celery.celery_config:celery_app purge -f
    
    Write-Host "✅ Tasks limpas" -ForegroundColor $Green
}

function Show-Help {
    Write-Host "`n🚀 EVAonline MATOPIBA - Gerenciador Celery + Redis" -ForegroundColor $Cyan
    Write-Host "="*60
    Write-Host "`nComandos disponíveis:" -ForegroundColor $Yellow
    Write-Host "  start-all      Inicia Redis, Worker, Beat e Flower"
    Write-Host "  stop-all       Para todos os serviços"
    Write-Host "  start-redis    Inicia apenas Redis"
    Write-Host "  stop-redis     Para Redis"
    Write-Host "  start-worker   Inicia Celery Worker"
    Write-Host "  stop-worker    Para Celery Worker"
    Write-Host "  start-beat     Inicia Celery Beat"
    Write-Host "  stop-beat      Para Celery Beat"
    Write-Host "  start-flower   Inicia Flower (interface web)"
    Write-Host "  stop-flower    Para Flower"
    Write-Host "  test           Executa testes de integração"
    Write-Host "  status         Mostra status dos serviços"
    Write-Host "  logs           Mostra logs recentes"
    Write-Host "  trigger        Executa task MATOPIBA manualmente"
    Write-Host "  purge          Limpa tasks pendentes"
    Write-Host "  help           Mostra esta ajuda"
    Write-Host "`n" + "="*60
}

# ============================================================================
# Comandos Principais
# ============================================================================

switch ($Command) {
    'start-all' {
        Write-Host "`n🚀 INICIANDO TODOS OS SERVIÇOS" -ForegroundColor $Cyan
        Start-Redis
        Start-Sleep -Seconds 2
        Start-CeleryWorker
        Start-Sleep -Seconds 2
        Start-CeleryBeat
        Start-Sleep -Seconds 2
        Start-Flower
        Write-Host "`n✅ Todos os serviços iniciados!" -ForegroundColor $Green
        Write-Host "💡 Use 'status' para verificar o estado dos serviços" -ForegroundColor $Yellow
    }
    
    'stop-all' {
        Write-Host "`n🛑 PARANDO TODOS OS SERVIÇOS" -ForegroundColor $Cyan
        Stop-Flower
        Stop-CeleryBeat
        Stop-CeleryWorker
        Stop-Redis
        Write-Host "`n✅ Todos os serviços parados!" -ForegroundColor $Green
    }
    
    'start-redis' { Start-Redis }
    'stop-redis' { Stop-Redis }
    'start-worker' { Start-CeleryWorker }
    'stop-worker' { Stop-CeleryWorker }
    'start-beat' { Start-CeleryBeat }
    'stop-beat' { Stop-CeleryBeat }
    'start-flower' { Start-Flower }
    'stop-flower' { Stop-Flower }
    'test' { Test-Integration }
    'status' { Get-Status }
    'logs' { Get-Logs }
    'trigger' { Invoke-TaskManually }
    'purge' { Clear-Tasks }
    'help' { Show-Help }
    default { Show-Help }
}
