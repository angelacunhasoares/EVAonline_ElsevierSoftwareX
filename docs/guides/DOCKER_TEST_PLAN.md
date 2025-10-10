# 🚀 Plano de Execução - Teste Docker EVA Online

**Data:** 09 de outubro de 2025  
**Duração estimada:** 15-30 minutos  
**Objetivo:** Validar aplicação completa em Docker com vetorização ETo

---

## 📋 Checklist Pré-Teste

Antes de iniciar, confirmar:

- [ ] Docker Desktop rodando (Windows)
- [ ] PowerShell aberto como Administrador
- [ ] Navegador pronto (Chrome/Edge/Firefox)
- [ ] Terminal com path do projeto:
  ```powershell
  cd C:\Users\User\OneDrive\Documentos\GitHub\EVAonline_ElsevierSoftwareX
  ```

---

## 🎬 Fase 1: Build e Inicialização (5-10 min)

### Passo 1: Build das Imagens

```powershell
# Limpar containers antigos (opcional)
docker-compose down -v

# Build completo (primeira vez ~5-10 min)
docker-compose build

# Verificar imagens criadas
docker images | Select-String "evaonline"
```

**Imagens esperadas:**
- `evaonline_backend:latest`
- `evaonline_frontend:latest`
- `evaonline_celery_worker:latest`
- Mais: postgres:15, redis:7-alpine

### Passo 2: Iniciar Serviços

```powershell
# Iniciar todos em background
docker-compose up -d

# Verificar status (aguardar ~30s para inicialização)
Start-Sleep -Seconds 30
docker-compose ps
```

**Status esperado (7 serviços):**
```
NAME                         STATUS    PORTS
evaonline_backend            Up        0.0.0.0:8000->8000/tcp
evaonline_celery_beat        Up
evaonline_celery_worker      Up
evaonline_flower             Up        0.0.0.0:5555->5555/tcp
evaonline_frontend           Up        0.0.0.0:8050->8050/tcp
evaonline_postgres           Up        0.0.0.0:5432->5432/tcp
evaonline_redis              Up        0.0.0.0:6379->6379/tcp
```

✅ **CHECKPOINT 1:** Todos serviços "Up"? → Continuar  
❌ Se algum "Exit" ou "Restarting" → Ver logs: `docker-compose logs [service_name]`

### Passo 3: Verificar Logs de Inicialização

```powershell
# Backend
docker-compose logs backend | Select-String -Pattern "Uvicorn running|Application startup complete"

# Celery Worker
docker-compose logs celery_worker | Select-String -Pattern "ready|connected"

# Frontend
docker-compose logs frontend | Select-String -Pattern "Dash is running|Running on"
```

✅ **CHECKPOINT 2:** Mensagens de "running" aparecem? → Continuar

---

## 🧪 Fase 2: Validação de Serviços (10-15 min)

### Teste 1: Backend Health Check (30s)

```powershell
# PowerShell
Invoke-RestMethod http://localhost:8000/health | ConvertTo-Json -Depth 3
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-09T...",
  "services": {
    "database": "connected",
    "redis": "connected",
    "celery": "running"
  }
}
```

✅ **CHECKPOINT 3:** Status "healthy"? → Continuar  
❌ Se erro → Verificar PostgreSQL/Redis: `docker-compose ps`

### Teste 2: Frontend MATOPIBA (2 min)

**Abrir navegador:** http://localhost:8050

**Verificar:**
1. [ ] Página carrega sem erros
2. [ ] Navbar com menu "MATOPIBA Forecast"
3. [ ] Click na aba "MATOPIBA Forecast"
4. [ ] Mapa com 337 cidades aparece
5. [ ] Seletores de variáveis (ETo, Temp, etc.)
6. [ ] Seletor de dias (Hoje, Amanhã)

✅ **CHECKPOINT 4:** Frontend carrega completamente? → Continuar

**Screenshot sugerido:**
- Tirar print do mapa MATOPIBA com 337 cidades visíveis

### Teste 3: PostgreSQL Connection (1 min)

```powershell
# Entrar no container PostgreSQL
docker-compose exec postgres psql -U postgres -d evaonline

# Dentro do psql:
# \dt                                    # Listar tabelas
# SELECT COUNT(*) FROM matopiba_cities;  # Deve retornar 337
# \q                                     # Sair
```

**Comandos completos:**
```powershell
docker-compose exec postgres psql -U postgres -d evaonline -c "\dt"
docker-compose exec postgres psql -U postgres -d evaonline -c "SELECT COUNT(*) FROM matopiba_cities;"
```

**Resultado esperado:**
```
 count
-------
   337
(1 row)
```

✅ **CHECKPOINT 5:** Retorna 337? → Continuar

### Teste 4: Redis Cache (1 min)

```powershell
# Entrar no Redis
docker-compose exec redis redis-cli

# Comandos Redis:
# KEYS matopiba:*
# INFO memory
# exit
```

**Comandos completos:**
```powershell
docker-compose exec redis redis-cli KEYS "matopiba:*"
docker-compose exec redis redis-cli INFO memory | Select-String "used_memory_human"
```

✅ **CHECKPOINT 6:** Redis responde? → Continuar

### Teste 5: Trigger Manual ETo (3-5 min) ⭐ **CRÍTICO**

```powershell
# Entrar no container backend
docker-compose exec backend bash

# Executar trigger vetorizado
python scripts/trigger_matopiba_forecast.py
```

**Interação esperada:**
```
======================================================================
🚀 TRIGGER MANUAL: Cálculo ETo MATOPIBA
======================================================================

⚠️  Este script chama a função DIRETAMENTE (sem Celery)
    Tempo estimado: ~60-90 segundos para 337 cidades

Continuar? (s/N): s
```

**Digite:** `s` + Enter

**Aguardar processamento...**

**Resultado esperado (~2 min):**
```
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
  Amostras:             674
  Status:               BOM

======================================================================
⚡ PERFORMANCE
======================================================================

Tempo total:     ~1.6 segundos (337 cidades)
Throughput:      6000-9500 registros/segundo
```

✅ **CHECKPOINT 7:** Métricas aparecem corretamente?
- [ ] R² entre 0.75-0.76
- [ ] RMSE < 1.2 mm/dia
- [ ] Tempo < 2 segundos
- [ ] Status = "BOM"

❌ Se falhar → Verificar logs: `docker-compose logs celery_worker`

**Sair do container:**
```bash
exit
```

### Teste 6: Celery Flower Monitor (1 min)

**Abrir navegador:** http://localhost:5555

**Verificar:**
1. [ ] Dashboard Flower carrega
2. [ ] Workers ativos: 1 (evaonline_celery_worker)
3. [ ] Tasks agendados visíveis
4. [ ] Gráfico de throughput mostra atividade

✅ **CHECKPOINT 8:** Flower acessível? → Continuar

### Teste 7: Celery Beat Schedule (2 min)

```powershell
# Ver tarefas agendadas
docker-compose exec celery_beat celery -A backend.infrastructure.celery.celery_config inspect scheduled

# Ver tarefas ativas
docker-compose exec celery_worker celery -A backend.infrastructure.celery.celery_config inspect active
```

**Verificar schedule:**
- `update-matopiba-forecasts-00h` → 00:00 BRT
- `update-matopiba-forecasts-06h` → 06:00 BRT
- `update-matopiba-forecasts-12h` → 12:00 BRT
- `update-matopiba-forecasts-18h` → 18:00 BRT

✅ **CHECKPOINT 9:** Tasks aparecem no schedule? → Continuar

---

## 📊 Fase 3: Validação Final (5 min)

### Checklist de Sucesso

#### Serviços
- [ ] ✅ Backend responde em http://localhost:8000/health
- [ ] ✅ Frontend carrega em http://localhost:8050
- [ ] ✅ PostgreSQL conectado (337 cidades)
- [ ] ✅ Redis conectado e respondendo
- [ ] ✅ Celery worker ativo
- [ ] ✅ Celery beat com schedule
- [ ] ✅ Flower monitor acessível

#### Performance
- [ ] ✅ Trigger ETo < 2 segundos
- [ ] ✅ R² = 0.757 ± 0.01
- [ ] ✅ RMSE < 1.2 mm/dia
- [ ] ✅ Throughput > 5000 rec/s

#### Frontend
- [ ] ✅ Mapa MATOPIBA com 337 cidades
- [ ] ✅ Seletores de variáveis funcionais
- [ ] ✅ Status bar atualizado
- [ ] ✅ Sem erros no console do navegador

### Métricas Finais

```powershell
# Ver uso de recursos
docker stats --no-stream

# Ver espaço em disco
docker system df
```

**Uso esperado:**
- **CPU:** <50% em idle, picos 80-100% durante cálculo
- **Memória:** ~2-4 GB total (todos containers)
- **Disco:** ~2-3 GB (imagens + volumes)

---

## 📸 Evidências Sugeridas

Para documentação, capturar:

1. **Screenshot:** Frontend MATOPIBA com mapa 337 cidades
2. **Screenshot:** Flower dashboard com workers ativos
3. **Log:** Output completo do trigger manual (métricas)
4. **Screenshot:** `docker-compose ps` com todos serviços "Up"

---

## 🛑 Shutdown

Após testes bem-sucedidos:

```powershell
# Parar containers (preserva dados)
docker-compose stop

# Ou parar e remover (mantém volumes)
docker-compose down

# Ver logs finais
docker-compose logs --tail=50 celery_worker > logs_celery_final.txt
```

---

## ❌ Troubleshooting Rápido

### Problema: Backend não inicia

```powershell
# Ver erro específico
docker-compose logs backend

# Rebuild forçado
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Problema: PostgreSQL connection refused

```powershell
# Verificar se está rodando
docker-compose ps postgres

# Restart
docker-compose restart postgres

# Aguardar inicialização
Start-Sleep -Seconds 10

# Testar conexão
docker-compose exec postgres psql -U postgres -c "SELECT 1"
```

### Problema: Celery worker não processa

```powershell
# Ver logs
docker-compose logs celery_worker

# Restart
docker-compose restart celery_worker

# Verificar conexão Redis
docker-compose exec celery_worker python -c "import redis; r=redis.Redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

### Problema: Frontend não carrega mapa

```powershell
# Ver logs
docker-compose logs frontend

# Verificar cache Redis
docker-compose exec redis redis-cli KEYS "matopiba:*"

# Se vazio, popular com trigger
docker-compose exec backend python scripts/trigger_matopiba_forecast.py
```

---

## 🎯 Critérios de Sucesso

**Teste APROVADO se:**
- ✅ Todos 9 checkpoints passaram
- ✅ Trigger manual < 2 segundos
- ✅ R² = 0.757 ± 0.01
- ✅ RMSE < 1.2 mm/dia
- ✅ Frontend MATOPIBA funcional
- ✅ Sem erros nos logs

**Se APROVADO:**
- ✅ Deploy Docker validado
- ✅ Vetorização funcionando em produção
- ✅ Pronto para ambiente de staging/produção

---

## 📞 Suporte

**Documentação de referência:**
- [Guia Docker Testing](../docs/guides/DOCKER_TESTING_GUIDE.md)
- [Relatório Vetorização](../docs/VECTORIZATION_REPORT.md)
- [Status do Projeto](../docs/PROJECT_STATUS.md)

**Em caso de problemas:**
1. Verificar logs específicos: `docker-compose logs [service]`
2. Consultar troubleshooting no DOCKER_TESTING_GUIDE.md
3. Verificar recursos: `docker stats`
4. Rebuild completo: `docker-compose down -v && docker-compose build --no-cache && docker-compose up -d`

---

**Boa sorte nos testes! 🚀**

**Estimativa total:** 15-30 minutos  
**Última atualização:** 09 de outubro de 2025
