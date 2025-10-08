#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script PowerShell para executar testes de integração EVAonline

.DESCRIPTION
    Este script facilita a execução dos testes de integração,
    verificando pré-requisitos e iniciando serviços necessários.

.PARAMETER Quick
    Executa apenas testes rápidos (conectividade)

.PARAMETER Full
    Executa todos os testes (padrão)

.PARAMETER StartServices
    Inicia Redis e PostgreSQL automaticamente via Docker

.PARAMETER Verbose
    Mostra output detalhado

.EXAMPLE
    .\run_tests.ps1
    Executa todos os testes

.EXAMPLE
    .\run_tests.ps1 -Quick
    Executa apenas testes rápidos

.EXAMPLE
    .\run_tests.ps1 -StartServices
    Inicia serviços e executa testes
#>

param(
    [switch]$Quick,
    [switch]$Full,
    [switch]$StartServices,
    [switch]$Verbose
)

# Cores para output
function Write-Success { Write-Host "✅ $args" -ForegroundColor Green }
function Write-Info { Write-Host "ℹ️  $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "⚠️  $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "❌ $args" -ForegroundColor Red }

# Banner
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "🧪 TESTES DE INTEGRAÇÃO - EVAonline Infrastructure" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Verificar se está no diretório correto
$currentDir = Get-Location
if (-not (Test-Path ".\tests\integration")) {
    Write-Error "Execute este script a partir do diretório raiz do projeto!"
    exit 1
}

# Verificar ambiente virtual
Write-Info "Verificando ambiente virtual..."
if (Test-Path ".\.venv\Scripts\activate.ps1") {
    Write-Success "Ambiente virtual encontrado"
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Warning "Ambiente virtual não encontrado em .\.venv"
    Write-Info "Tentando usar Python do sistema..."
}

# Verificar Python
Write-Info "Verificando Python..."
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Success "Python: $pythonVersion"
} else {
    Write-Error "Python não encontrado!"
    exit 1
}

# Verificar pytest
Write-Info "Verificando pytest..."
python -m pytest --version 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Success "pytest instalado"
} else {
    Write-Error "pytest não encontrado!"
    Write-Info "Instalando pytest..."
    pip install pytest
}

# Iniciar serviços se solicitado
if ($StartServices) {
    Write-Info "Iniciando serviços Docker..."
    
    # Verificar se Docker está rodando
    docker ps 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker não está rodando!"
        Write-Info "Inicie o Docker Desktop e tente novamente"
        exit 1
    }
    
    Write-Info "Subindo Redis e PostgreSQL..."
    docker-compose up -d redis postgres
    
    Write-Info "Aguardando serviços ficarem prontos (30 segundos)..."
    Start-Sleep -Seconds 30
    
    # Verificar se serviços estão rodando
    $redisRunning = docker ps | Select-String "redis"
    $postgresRunning = docker ps | Select-String "postgres"
    
    if ($redisRunning) {
        Write-Success "Redis está rodando"
    } else {
        Write-Warning "Redis pode não estar rodando"
    }
    
    if ($postgresRunning) {
        Write-Success "PostgreSQL está rodando"
    } else {
        Write-Warning "PostgreSQL pode não estar rodando"
    }
    
    Write-Host ""
}

# Construir comando pytest
$pytestCmd = @("python", "-m", "pytest", "tests\integration\test_infrastructure_integration.py")

if ($Verbose) {
    $pytestCmd += @("-v", "-s")
} else {
    $pytestCmd += "-v"
}

$pytestCmd += @("--tb=short", "--color=yes")

# Filtrar testes se Quick
if ($Quick) {
    Write-Info "Modo RÁPIDO: Executando apenas testes de conectividade"
    $pytestCmd += @("-k", "TestConnectivity or TestRedisCache")
} else {
    Write-Info "Modo COMPLETO: Executando todos os testes"
}

Write-Host ""
Write-Info "Comando: $($pytestCmd -join ' ')"
Write-Host ""

# Executar testes
try {
    & $pytestCmd[0] $pytestCmd[1..($pytestCmd.Length-1)]
    $exitCode = $LASTEXITCODE
} catch {
    Write-Error "Erro ao executar testes: $_"
    $exitCode = 1
}

# Resultado final
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
if ($exitCode -eq 0) {
    Write-Success "TODOS OS TESTES PASSARAM!"
} else {
    Write-Error "ALGUNS TESTES FALHARAM"
    Write-Info "Veja os logs acima para detalhes"
}
Write-Host "=" * 70 -ForegroundColor Cyan

exit $exitCode
