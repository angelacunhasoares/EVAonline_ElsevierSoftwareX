# Guia de Teste Docker - EVA Online MATOPIBA

**Data:** 09 de outubro de 2025  
**Objetivo:** Testar aplicação completa no Docker com vetorização ETo

---

## 📋 Pré-requisitos

### Software Necessário

```bash
# Verificar instalações
docker --version          # Docker Engine 20.10+
docker-compose --version  # Docker Compose 1.29+
```

### Serviços Docker

A aplicação usa os seguintes containers:

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| **backend** | 8000 | FastAPI + Uvicorn |
| **frontend** | 8050 | Dash app (UI) |
| **postgres** | 5432 | PostgreSQL 15 |
| **redis** | 6379 | Cache Redis 7 |
| **celery_worker** | - | Worker Celery (ETo tasks) |
| **celery_beat** | - | Scheduler (4x/dia MATOPIBA) |
| **flower** | 5555 | Monitor Celery |

---

## 🚀 Inicialização

### 1. Build das Imagens

```powershell
# Na raiz do projeto
cd C:\Users\User\OneDrive\Documentos\GitHub\EVAonline_ElsevierSoftwareX

# Build completo (primeira vez ou após mudanças)
docker-compose build

# Build forçado (ignora cache)
docker-compose build --no-cache
```

### 2. Iniciar Todos os Serviços

```powershell
# Iniciar em background
docker-compose up -d

# Iniciar com logs visíveis (Ctrl+C para parar)
docker-compose up

# Verificar status
docker-compose ps
```

**Saída esperada:**
```
       Name                      Command               State           Ports
-------------------------------------------------------------------------------------
evaonline_backend        uvicorn main:app --host ...   Up      0.0.0.0:8000->8000/tcp
evaonline_celery_beat    celery -A backend.infra ...   Up
evaonline_celery_worker  celery -A backend.infra ...   Up
evaonline_flower         celery -A backend.infra ...   Up      0.0.0.0:5555->5555/tcp
evaonline_frontend       python frontend/app.py         Up      0.0.0.0:8050->8050/tcp
evaonline_postgres       docker-entrypoint.sh pos ...   Up      0.0.0.0:5432->5432/tcp
evaonline_redis          docker-entrypoint.sh red ...   Up      0.0.0.0:6379->6379/tcp
```

### 3. Verificar Logs

```powershell
# Logs de todos os serviços
docker-compose logs -f

# Logs de serviço específico
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f frontend

# Últimas 50 linhas
docker-compose logs --tail=50 celery_worker
```

---

## 🧪 Testes de Validação

### Teste 1: Health Check Backend

```powershell
# PowerShell
Invoke-RestMethod http://localhost:8000/health

# Ou no navegador
# http://localhost:8000/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-09T18:30:00Z",
  "services": {
    "database": "connected",
    "redis": "connected",
    "celery": "running"
  }
}
```

### Teste 2: Frontend MATOPIBA

1. Abrir navegador: `http://localhost:8050`
2. Navegar para aba **"MATOPIBA Forecast"**
3. Verificar:
   - ✅ Mapa com 337 cidades carregado
   - ✅ Seletor de variáveis (ETo, Temp, Umidade, etc.)
   - ✅ Seletor de dias (Hoje, Amanhã)
   - ✅ Status bar: "Última atualização: HH:MM"

### Teste 3: Trigger Manual ETo MATOPIBA

```powershell
# Entrar no container backend
docker-compose exec backend bash

# Executar trigger manual (vetorizado)
python scripts/trigger_matopiba_forecast.py
```

**Saída esperada:**
```
======================================================================
🚀 TRIGGER MANUAL: Cálculo ETo MATOPIBA
======================================================================

⚠️  Este script chama a função DIRETAMENTE (sem Celery)
    Tempo estimado: ~60-90 segundos para 337 cidades

Continuar? (s/N): s

1️⃣ Buscando dados Open-Meteo...
✅ Dados recebidos: 337 cidades

2️⃣ Calculando ETo (método vetorizado)...
✅ Cálculo concluído: 337 cidades

======================================================================
📊 MÉTRICAS DE VALIDAÇÃO (APÓS VETORIZAÇÃO)
======================================================================

  R² (correlação):      0.7567
  RMSE (erro):          1.066 mm/dia
  Bias (viés):          0.832 mm/dia
  MAE (erro absoluto):  0.834 mm/dia
  Amostras:             674
  Status:               BOM

======================================================================
⚡ PERFORMANCE
======================================================================

Tempo total:     ~1.6 segundos (337 cidades)
Throughput:      6000-9500 registros/segundo
Speedup:         5x vs versão loop
```

### Teste 4: Celery Beat (Agendamento Automático)

```powershell
# Ver schedule das tarefas
docker-compose exec celery_beat celery -A backend.infrastructure.celery.celery_config inspect scheduled

# Forçar execução imediata (debugging)
docker-compose exec celery_worker celery -A backend.infrastructure.celery.celery_config call update_matopiba_forecasts
```

**Schedule configurado (celery_config.py):**
- 00:00 BRT - Atualização noturna
- 06:00 BRT - Atualização manhã
- 12:00 BRT - Atualização meio-dia
- 18:00 BRT - Atualização tarde

### Teste 5: Redis Cache

```powershell
# Entrar no container Redis
docker-compose exec redis redis-cli

# Comandos Redis
127.0.0.1:6379> KEYS matopiba:*
127.0.0.1:6379> GET "matopiba:forecasts:today_tomorrow"
127.0.0.1:6379> TTL "matopiba:forecasts:today_tomorrow"
127.0.0.1:6379> INFO memory
```

**Keys esperadas:**
```
1) "matopiba:forecasts:today_tomorrow"
2) "matopiba:cities:337"
3) "matopiba:validation:metrics"
```

### Teste 6: PostgreSQL Database

```powershell
# Entrar no container PostgreSQL
docker-compose exec postgres psql -U postgres -d evaonline

# Queries de validação
\dt                                    # Listar tabelas
SELECT COUNT(*) FROM eto_data;         # Total de registros
SELECT COUNT(*) FROM matopiba_cities;  # 337 cidades

# Ver últimas atualizações MATOPIBA
SELECT city_code, city_name, last_updated 
FROM matopiba_forecasts 
ORDER BY last_updated DESC 
LIMIT 10;

# Validar R² por cidade (top 10)
SELECT city_name, r2_score, rmse, bias 
FROM matopiba_validation 
ORDER BY r2_score DESC 
LIMIT 10;
```

### Teste 7: Flower (Monitor Celery)

1. Abrir navegador: `http://localhost:5555`
2. Verificar:
   - ✅ Workers ativos: 1 (evaonline_celery_worker)
   - ✅ Tasks agendados: `update_matopiba_forecasts`
   - ✅ Tasks executados recentemente
   - ✅ Throughput: ~6000-9000 rec/s

---

## 📊 Validação de Performance

### Benchmark ETo Vetorizado

```powershell
# No container backend
docker-compose exec backend python

>>> from backend.core.eto_calculation.eto_matopiba import calculate_eto_matopiba_batch
>>> from backend.api.services.openmeteo_matopiba_client import OpenMeteoMatopibaClient
>>> import time
>>> 
>>> # Fetch data
>>> client = OpenMeteoMatopibaClient()
>>> forecasts, _ = client.get_forecasts_all_cities()
>>> 
>>> # Benchmark
>>> t_start = time.time()
>>> results, _ = calculate_eto_matopiba_batch(forecasts)
>>> t_elapsed = time.time() - t_start
>>> 
>>> print(f"Tempo: {t_elapsed:.2f}s para {len(results)} cidades")
>>> print(f"Throughput: {len(results) * 48 / t_elapsed:.0f} registros/s")
```

**Resultado esperado:**
```
Tempo: 1.6s para 337 cidades
Throughput: 10120 registros/s
```

---

## 🐛 Troubleshooting

### Problema 1: Container não inicia

**Sintoma:** `docker-compose up` falha

**Solução:**
```powershell
# Verificar logs específicos
docker-compose logs backend

# Rebuild forçado
docker-compose build --no-cache backend
docker-compose up -d backend

# Verificar recursos
docker stats
```

### Problema 2: PostgreSQL connection refused

**Sintoma:** `psycopg2.OperationalError: could not connect`

**Solução:**
```powershell
# Verificar se Postgres está running
docker-compose ps postgres

# Restart do serviço
docker-compose restart postgres

# Verificar variáveis de ambiente
docker-compose exec backend env | grep POSTGRES
```

### Problema 3: Redis cache vazio

**Sintoma:** Frontend não mostra dados MATOPIBA

**Solução:**
```powershell
# Trigger manual para popular cache
docker-compose exec backend python scripts/trigger_matopiba_forecast.py

# Verificar Redis
docker-compose exec redis redis-cli
127.0.0.1:6379> KEYS matopiba:*

# Se vazio, executar warm-up
docker-compose exec celery_worker celery -A backend.infrastructure.celery.celery_config call update_matopiba_forecasts
```

### Problema 4: Celery worker não processa tasks

**Sintoma:** Tasks ficam em `PENDING` no Flower

**Solução:**
```powershell
# Verificar se worker está ativo
docker-compose logs celery_worker

# Restart do worker
docker-compose restart celery_worker

# Verificar conexão Redis
docker-compose exec celery_worker python -c "from backend.infrastructure.celery.celery_config import celery_app; print(celery_app.connection().as_uri())"

# Purgar fila (CUIDADO!)
docker-compose exec celery_worker celery -A backend.infrastructure.celery.celery_config purge
```

### Problema 5: Frontend não carrega mapa

**Sintoma:** Erro 404 ou componente vazio

**Solução:**
```powershell
# Verificar logs frontend
docker-compose logs frontend

# Verificar assets
docker-compose exec frontend ls -la frontend/assets/images/

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

---

## 🔧 Configurações Importantes

### Variáveis de Ambiente (.env)

```ini
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha_segura
POSTGRES_DB=evaonline
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Open-Meteo API
OPENMETEO_RATE_LIMIT=10
OPENMETEO_TIMEOUT=30

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# App
DEBUG=False
SECRET_KEY=sua_chave_secreta_aqui
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Docker Compose Profiles

```powershell
# Apenas serviços essenciais (dev)
docker-compose --profile dev up

# Produção completa (todos serviços)
docker-compose --profile prod up

# Apenas backend + workers (sem frontend)
docker-compose --profile api up
```

---

## 📈 Métricas de Sucesso

### Checklist de Validação

- [ ] ✅ Backend responde em `http://localhost:8000/health`
- [ ] ✅ Frontend carrega em `http://localhost:8050`
- [ ] ✅ PostgreSQL aceita conexões (port 5432)
- [ ] ✅ Redis aceita conexões (port 6379)
- [ ] ✅ Celery worker processa tasks
- [ ] ✅ Celery beat agenda tarefas (4x/dia)
- [ ] ✅ Flower monitor acessível em `http://localhost:5555`
- [ ] ✅ Trigger manual ETo < 2 segundos (337 cidades)
- [ ] ✅ R² validação = 0.757 ± 0.01
- [ ] ✅ RMSE < 1.2 mm/dia
- [ ] ✅ Cache Redis populado com forecasts
- [ ] ✅ Frontend exibe mapas MATOPIBA
- [ ] ✅ Logs sem erros críticos

### Performance Targets

| Métrica | Target | Medido |
|---------|--------|--------|
| **Tempo ETo batch** | <2s | 1.6s ✅ |
| **Throughput** | >5000 rec/s | 6000-9500 rec/s ✅ |
| **R² validação** | >0.7 | 0.757 ✅ |
| **RMSE** | <1.5 mm/dia | 1.07 mm/dia ✅ |
| **Uptime workers** | >99% | - |
| **Cache hit rate** | >95% | - |

---

## 🛑 Shutdown

```powershell
# Parar todos os containers (preserva volumes)
docker-compose stop

# Parar e remover containers (preserva volumes)
docker-compose down

# Parar, remover containers E volumes (⚠️ PERDE DADOS!)
docker-compose down -v

# Limpar tudo (imagens, containers, volumes)
docker-compose down -v --rmi all
```

---

## 📚 Documentação Adicional

- **Vetorização ETo:** `docs/VECTORIZATION_REPORT.md`
- **API Backend:** `http://localhost:8000/docs` (Swagger)
- **Arquitetura:** `docs/architecture.mmd`
- **Testes:** `backend/tests/TESTING_GUIDE.md`

---

## 🔗 Links Úteis

- Frontend: http://localhost:8050
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Flower Monitor: http://localhost:5555
- Adminer (DB GUI): http://localhost:8080 (se habilitado)

---

**Última atualização:** 09 de outubro de 2025  
**Status:** ✅ Pronto para teste Docker completo
