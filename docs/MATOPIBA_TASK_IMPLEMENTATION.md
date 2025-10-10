# 🚀 MATOPIBA Task - Implementação Completa

## ✅ O Que Foi Implementado

### 1️⃣ **Celery Task Otimizada** (`matopiba_forecast_task.py`)

**Pipeline Completo (5 steps)**:
```
STEP 1: Buscar Open-Meteo (337 cidades × 2 dias) → 2-5 min
STEP 2: Calcular ETo EVAonline (Penman-Monteith)
STEP 3: Validar (R², RMSE, Bias) - NÃO BLOQUEANTE
STEP 4: Redis cache "quente" (TTL 6h) → latência <100ms ✅
STEP 5: PostgreSQL histórico → auditoria/recovery ✅
```

**Melhorias Implementadas**:
- ✅ **Run Scheduling**: 00h, 06h, 12h, 18h UTC (crontab exato)
- ✅ **Run Labels**: "Run 00h UTC", "Run 06h UTC", etc.
- ✅ **Cleanup Automático**: Deleta chaves Redis antigas
- ✅ **Qualidade Check**: EXCELENTE / ACEITÁVEL / ABAIXO DO ESPERADO
- ✅ **PostgreSQL Histórico**: Auditoria completa com JSONB metadata
- ✅ **Validação Não-Bloqueante**: Salva cache mesmo com qualidade baixa
- ✅ **Connection Pooling**: `pool_pre_ping=True` para PostgreSQL
- ✅ **Graceful Degradation**: Funciona sem PostgreSQL (logs warning)

---

### 2️⃣ **Redis Keys Atualizadas**

**ANTES**:
```
matopiba:forecasts:today_tomorrow  ❌ Confuso, não indica run
matopiba:metadata                   ❌ Sem versão
```

**DEPOIS**:
```
matopiba:forecasts:latest  ✅ Sempre aponta pro run atual
matopiba:metadata:latest   ✅ Metadata rápida
```

**TTL**: 6 horas (limpa automaticamente)

---

### 3️⃣ **PostgreSQL Histórico**

**Tabela**: `matopiba_runs`

```sql
CREATE TABLE matopiba_runs (
    id SERIAL PRIMARY KEY,
    run_label VARCHAR(50) NOT NULL,        -- "Run 00h UTC"
    updated_at TIMESTAMP NOT NULL UNIQUE,  -- Timestamp do run
    n_cities INTEGER NOT NULL,             -- 337 esperado
    r2 FLOAT,                              -- Correlação 0-1
    rmse FLOAT,                            -- Erro mm/dia
    bias FLOAT,                            -- Viés mm/dia
    success_rate FLOAT,                    -- % de sucesso
    quality VARCHAR(20),                   -- EXCELENTE/ACEITÁVEL/ABAIXO
    metadata_json JSONB,                   -- Metadata completa
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Índices**:
- `idx_matopiba_runs_updated_at` → Busca por data
- `idx_matopiba_runs_run_label` → Filtro por run
- `idx_matopiba_runs_quality` → Análise de qualidade

**Queries Úteis** (incluídas no SQL):
```sql
-- Últimos 10 runs
SELECT run_label, updated_at, quality, r2, rmse FROM matopiba_runs ORDER BY updated_at DESC LIMIT 10;

-- Runs com problemas
SELECT * FROM matopiba_runs WHERE quality = 'ABAIXO DO ESPERADO';
```

---

### 4️⃣ **Celery Schedule** (`celery_config.py`)

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'update-matopiba-forecasts': {
        'task': 'update_matopiba_forecasts',
        'schedule': crontab(hour='0,6,12,18', minute=0),  # Exato: 00h, 06h, 12h, 18h UTC
        'options': {'queue': 'matopiba_processing'}
    },
}
```

**Execução**:
- **00:00 UTC** → Run 00h UTC
- **06:00 UTC** → Run 06h UTC
- **12:00 UTC** → Run 12h UTC
- **18:00 UTC** → Run 18h UTC

---

## 📊 Benefícios

| Aspecto | ANTES | DEPOIS |
|---------|-------|--------|
| **Latência** | API call (2-5 min) por request | Redis cache (<100ms) ✅ |
| **Confiabilidade** | Sem histórico | PostgreSQL auditoria ✅ |
| **Escalabilidade** | Frontend bloqueia | Celery workers separados ✅ |
| **UX** | Flickering na UI | Dados fixos por run (6h) ✅ |
| **Custos** | Rate limits API | Cache reduz calls ✅ |
| **Manutenibilidade** | Código acoplado | Separação backend/frontend ✅ |
| **Monitoramento** | Sem histórico | PostgreSQL + Flower ✅ |

---

## 🔧 Setup Passo a Passo

### 1. **Criar Tabela PostgreSQL**
```bash
psql -U evaonline -d evaonline_db -f database/migrations/create_matopiba_runs_table.sql
```

### 2. **Configurar Variáveis de Ambiente** (`.env`)
```env
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Vazio para dev local

# PostgreSQL
DB_URL=postgresql://evaonline:evaonlinepassword@localhost:5432/evaonline_db
```

### 3. **Instalar Dependências**
```bash
pip install celery redis sqlalchemy psycopg2-binary
```

### 4. **Iniciar Celery Worker** (Terminal 1)
```bash
celery -A backend.infrastructure.celery.celery_app worker --loglevel=info --queue=matopiba_processing
```

### 5. **Iniciar Celery Beat** (Terminal 2)
```bash
celery -A backend.infrastructure.celery.celery_app beat --loglevel=info
```

### 6. **Monitorar com Flower** (Terminal 3, opcional)
```bash
celery -A backend.infrastructure.celery.celery_app flower --port=5555
```
Abrir: http://localhost:5555

---

## 🧪 Testes

### **Teste Manual da Task**
```python
from backend.infrastructure.celery.tasks.matopiba_forecast_task import update_matopiba_forecasts

# Executar task diretamente (sem Celery)
result = update_matopiba_forecasts()
print(result)
```

### **Verificar Cache Redis**
```bash
redis-cli
> GET matopiba:forecasts:latest
> TTL matopiba:forecasts:latest  # Deve mostrar tempo restante
```

### **Verificar Histórico PostgreSQL**
```sql
SELECT run_label, updated_at, n_cities, quality, r2, rmse 
FROM matopiba_runs 
ORDER BY updated_at DESC 
LIMIT 5;
```

---

## 📝 Logs

**Arquivo**: `logs/matopiba_task.log`

**Exemplo de Log**:
```
============================================================
INICIANDO Run 00h UTC: Update MATOPIBA (Task ID: abc123)
============================================================
✅ Redis conectado
✅ PostgreSQL conectado
STEP 1/5: Buscando previsões Open-Meteo para Run 00h UTC...
✅ Previsões obtidas: 337/337 cidades (100.0%)
STEP 2/5: Calculando ETo EVAonline para 337 cidades...
✅ ETo calculada: 337/337 cidades (100.0%)
STEP 3/5: Métricas de validação (Run 00h UTC)
  R² (correlação):      0.876
  RMSE (erro):          0.94 mm/dia
  Bias (viés):          0.12 mm/dia
✅ QUALIDADE: EXCELENTE (R²≥0.75, RMSE≤1.2)
STEP 4/5: Salvando Redis (cache quente)...
🧹 Cleanup: 2 chaves antigas deletadas
✅ Redis salvo (TTL: 6h, key: matopiba:forecasts:latest)
STEP 5/5: Salvando histórico PostgreSQL...
✅ PostgreSQL salvo (histórico Run 00h UTC)
============================================================
✅ CONCLUÍDO: Run 00h UTC (Update MATOPIBA)
Duração: 187.3 segundos (3.1 minutos)
Taxa de sucesso: 100.0% (337/337 cidades)
Qualidade: EXCELENTE
============================================================
```

---

## 🔍 Monitoramento

### **Métricas Importantes**
- **Taxa de Sucesso**: Deve ser ≥ 95% (≥320 cidades)
- **R²**: Deve ser ≥ 0.75 (EXCELENTE) ou ≥ 0.65 (ACEITÁVEL)
- **RMSE**: Deve ser ≤ 1.2 mm/dia (EXCELENTE) ou ≤ 1.5 (ACEITÁVEL)
- **Duração**: 2-5 minutos esperado

### **Alertas a Configurar**
- ❌ Task falha 3x consecutivas → Enviar email
- ⚠️ Taxa de sucesso < 90% → Alerta Slack
- ⚠️ Qualidade = "ABAIXO" → Revisar logs
- ⚠️ RMSE > 2.0 mm/dia → Investigar dados

---

## 🎯 Próximos Passos

1. ✅ **Task Implementada** → OK
2. ✅ **PostgreSQL Schema** → OK
3. ⏳ **Testar Celery Schedule** → Aguardando setup Redis + PostgreSQL
4. ⏳ **Monitorar com Flower** → Aguardando Celery workers ativos
5. ⏳ **Dashboard no Dash** → Próximo: exibir `run_label` e `quality` na UI

---

## 📚 Referências

- **Celery Docs**: https://docs.celeryq.dev/
- **Redis TTL**: https://redis.io/commands/ttl/
- **PostgreSQL JSONB**: https://www.postgresql.org/docs/current/datatype-json.html
- **Crontab Syntax**: https://crontab.guru/

---

**Autor**: EVAonline Team  
**Data**: 2025-10-10  
**Status**: ✅ Implementação Completa
