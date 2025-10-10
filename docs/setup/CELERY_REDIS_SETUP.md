# 🚀 Guia de Configuração: Redis + Celery para EVAonline MATOPIBA

## 📋 Visão Geral

Este guia configura o ambiente completo para execução das tarefas periódicas MATOPIBA:
- **Redis**: Cache e broker de mensagens
- **Celery Worker**: Processamento de tarefas assíncronas
- **Celery Beat**: Agendamento de tarefas periódicas (4x/dia)

## 🔧 Pré-requisitos

### 1. Verificar Redis Instalado

#### Windows (via Docker - RECOMENDADO):
```powershell
# Verificar se Docker está rodando
docker --version

# Se não tiver Docker, instalar do site oficial:
# https://www.docker.com/products/docker-desktop/
```

#### Linux/Mac:
```bash
redis-cli --version
# Se não instalado: sudo apt-get install redis-server (Ubuntu/Debian)
```

### 2. Verificar Python e Dependências

```powershell
# Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1

# Verificar pacotes instalados
pip list | Select-String -Pattern "celery|redis"

# Se necessário, instalar:
pip install celery[redis]==5.3.4 redis==5.0.1
```

## 🐳 Opção 1: Redis via Docker (RECOMENDADO)

### Iniciar Container Redis

```powershell
# Criar e iniciar Redis
docker run -d `
  --name evaonline-redis `
  -p 6379:6379 `
  -e REDIS_PASSWORD=evaonline `
  --restart unless-stopped `
  redis:7-alpine redis-server --requirepass evaonline

# Verificar se está rodando
docker ps | Select-String "redis"

# Testar conexão
docker exec -it evaonline-redis redis-cli -a evaonline PING
# Deve retornar: PONG
```

### Comandos Úteis Docker Redis

```powershell
# Parar Redis
docker stop evaonline-redis

# Iniciar Redis
docker start evaonline-redis

# Ver logs
docker logs evaonline-redis -f

# Remover container (CUIDADO: apaga dados)
docker rm -f evaonline-redis

# Executar comandos Redis
docker exec -it evaonline-redis redis-cli -a evaonline
# Dentro do CLI:
# > INFO
# > KEYS *
# > GET matopiba:metadata
# > FLUSHDB  # Limpa todos os dados (CUIDADO!)
```

## 💻 Opção 2: Redis Local (Windows)

### Instalar Redis via Chocolatey

```powershell
# Instalar Chocolatey se não tiver
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Instalar Redis
choco install redis-64 -y

# Iniciar serviço
redis-server --service-install
redis-server --service-start

# Testar
redis-cli ping
```

## ⚙️ Configurar Variáveis de Ambiente

### Criar arquivo `.env` na raiz do projeto:

```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=evaonline
REDIS_DB=0

# Celery Configuration
CELERY_BROKER_URL=redis://default:evaonline@localhost:6379/0
CELERY_RESULT_BACKEND=redis://default:evaonline@localhost:6379/0

# MATOPIBA Configuration
MATOPIBA_UPDATE_INTERVAL_HOURS=6
MATOPIBA_CACHE_TTL_HOURS=6
```

### Verificar Configuração

```powershell
# Executar script de teste
& .venv\Scripts\python.exe -c "
from backend.infrastructure.celery.celery_config import celery_app
print('✅ Celery configurado:', celery_app.conf.broker_url)
"
```

## 🏃 Iniciar Celery Worker

### Terminal 1: Worker Principal

```powershell
# Ativar venv
.\.venv\Scripts\Activate.ps1

# Iniciar worker
celery -A backend.infrastructure.celery.celery_config:celery_app worker `
  --loglevel=info `
  --pool=solo `
  --concurrency=4 `
  --hostname=worker@matopiba `
  --queues=general,eto_processing,data_download

# Explicação:
# --pool=solo         : Modo Windows (evita problemas de fork)
# --concurrency=4     : 4 tarefas paralelas
# --hostname=worker@matopiba : Nome identificador
# --queues=...        : Filas que o worker processa
```

### Terminal 2: Celery Beat (Agendador)

```powershell
# Ativar venv
.\.venv\Scripts\Activate.ps1

# Iniciar beat
celery -A backend.infrastructure.celery.celery_config:celery_app beat `
  --loglevel=info

# Beat agenda tarefas conforme celery_config.py
```

### Terminal 3: Monitor Flower (Opcional)

```powershell
# Instalar Flower
pip install flower

# Iniciar interface web
celery -A backend.infrastructure.celery.celery_config:celery_app flower `
  --port=5555

# Acessar: http://localhost:5555
```

## 🧪 Testar Configuração

### 1. Teste Básico Redis

```powershell
& .venv\Scripts\python.exe scripts\test_redis_connection.py
```

Crie o arquivo `scripts\test_redis_connection.py`:

```python
"""Teste de conexão Redis."""
import os
from redis import Redis

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "evaonline")
REDIS_URL = f"redis://default:{REDIS_PASSWORD}@localhost:6379/0"

try:
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    print("✅ Redis conectado com sucesso!")
    
    # Teste SET/GET
    redis_client.set("test_key", "test_value", ex=60)
    value = redis_client.get("test_key")
    print(f"✅ Teste SET/GET: {value}")
    
    redis_client.delete("test_key")
    print("✅ Todos os testes passaram!")
    
except Exception as e:
    print(f"❌ Erro ao conectar Redis: {e}")
```

### 2. Teste Task Celery

```powershell
& .venv\Scripts\python.exe -c "
from backend.infrastructure.celery.tasks.matopiba_forecast_task import update_matopiba_forecasts
result = update_matopiba_forecasts.delay()
print(f'✅ Task enviada: {result.id}')
print('Aguarde ~60-90s para conclusão...')
print(f'Status: {result.state}')
"
```

### 3. Teste Pipeline Completo

```powershell
# Executar teste de integração
& .venv\Scripts\python.exe -m backend.tests.test_matopiba_integration
```

## 📅 Configurar Agendamento 4x/dia

### Editar `celery_config.py`

Adicionar ao `beat_schedule`:

```python
# Atualização MATOPIBA - 4x por dia (00h, 06h, 12h, 18h BRT)
"update-matopiba-forecasts-00h": {
    "task": "update_matopiba_forecasts",
    "schedule": crontab(hour=0, minute=0),  # 00:00 BRT
},
"update-matopiba-forecasts-06h": {
    "task": "update_matopiba_forecasts",
    "schedule": crontab(hour=6, minute=0),  # 06:00 BRT
},
"update-matopiba-forecasts-12h": {
    "task": "update_matopiba_forecasts",
    "schedule": crontab(hour=12, minute=0),  # 12:00 BRT
},
"update-matopiba-forecasts-18h": {
    "task": "update_matopiba_forecasts",
    "schedule": crontab(hour=18, minute=0),  # 18:00 BRT
},
```

## 🔍 Monitoramento

### Ver Tasks Ativas

```powershell
# Via CLI
celery -A backend.infrastructure.celery.celery_config:celery_app inspect active

# Via Flower (interface web)
# http://localhost:5555/tasks
```

### Ver Logs

```powershell
# Worker logs (direto no terminal onde worker roda)

# Ou via arquivo
Get-Content .\logs\matopiba_task.log -Tail 50 -Wait
```

### Verificar Cache Redis

```powershell
# Via Docker
docker exec -it evaonline-redis redis-cli -a evaonline

# Dentro do Redis CLI:
KEYS matopiba:*
GET matopiba:metadata
TTL matopiba:forecasts:today_tomorrow
```

## 🐛 Troubleshooting

### Erro: "Connection refused" (Redis)

```powershell
# Verificar se Redis está rodando
docker ps | Select-String "redis"

# Se não, iniciar:
docker start evaonline-redis

# Ou criar novo:
docker run -d --name evaonline-redis -p 6379:6379 -e REDIS_PASSWORD=evaonline redis:7-alpine redis-server --requirepass evaonline
```

### Erro: "No module named 'celery'"

```powershell
# Instalar celery
pip install celery[redis]==5.3.4 redis==5.0.1
```

### Task não executa

```powershell
# 1. Verificar worker está rodando
celery -A backend.infrastructure.celery.celery_config:celery_app inspect ping

# 2. Verificar filas
celery -A backend.infrastructure.celery.celery_config:celery_app inspect registered

# 3. Limpar tasks antigas
celery -A backend.infrastructure.celery.celery_config:celery_app purge
```

### Task demora muito

```powershell
# Verificar número de cidades sendo processadas
# Reduzir temporariamente em matopiba_forecast_task.py:

# Testar com 10 cidades primeiro
# cities_df = client.cities_df.head(10)  # ← Adicionar esta linha
```

## 📊 Performance Esperada

- **1 cidade**: ~100ms
- **10 cidades**: ~1-2s
- **50 cidades**: ~5-10s
- **337 cidades**: ~60-90s

## ✅ Checklist Pré-Produção

- [ ] Redis rodando e acessível
- [ ] Celery worker iniciado e respondendo
- [ ] Celery beat agendado para 4x/dia
- [ ] Teste manual executado com sucesso
- [ ] Logs configurados e funcionando
- [ ] Flower instalado para monitoramento
- [ ] Backup/restore Redis configurado
- [ ] Variáveis de ambiente configuradas
- [ ] Documentação atualizada

## 🚀 Comandos Rápidos

```powershell
# Iniciar tudo (em terminais separados):

# Terminal 1: Redis
docker start evaonline-redis

# Terminal 2: Worker
.\.venv\Scripts\Activate.ps1
celery -A backend.infrastructure.celery.celery_config:celery_app worker --loglevel=info --pool=solo --concurrency=4

# Terminal 3: Beat
.\.venv\Scripts\Activate.ps1
celery -A backend.infrastructure.celery.celery_config:celery_app beat --loglevel=info

# Terminal 4: Flower
.\.venv\Scripts\Activate.ps1
celery -A backend.infrastructure.celery.celery_config:celery_app flower --port=5555

# Terminal 5: Testar
.\.venv\Scripts\Activate.ps1
python -m backend.tests.test_matopiba_integration
```

## 📚 Próximos Passos

1. ✅ Configurar Redis
2. ✅ Iniciar Celery Worker
3. ✅ Configurar Beat (4x/dia)
4. ⏳ Teste manual task
5. ⏳ Monitorar primeira execução completa (337 cidades)
6. ⏳ Validar métricas R²/RMSE em produção
7. ⏳ Documentar processo de deploy

---

**Autor**: EVAonline Team  
**Data**: 2025-10-09  
**Versão**: 1.0.0
