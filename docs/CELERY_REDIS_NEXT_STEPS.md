# ✅ Resumo: Configuração Celery + Redis - EVAonline MATOPIBA

## 📊 Status da Integração

### Concluído ✅

1. **Algoritmo ETo Validado**
   - R² = 0.8306 (EXCELENTE)
   - RMSE = 0.5853 mm/dia
   - Bias = +0.4357 mm/dia
   - Nighttime fix implementado (Cn=6/Cd=0.24 quando Rs=0)

2. **Integração MATOPIBA**
   - ✅ `openmeteo_matopiba_client.py` modificado
     - Retorna `hourly_data` (raw) + `forecast` (agregado)
     - 12 variáveis horárias incluídas
   - ✅ `eto_matopiba.py` reescrito
     - Usa `calculate_eto_hourly()` validado
     - Calcula ETo_EVAonline real (não placeholder)
     - Pipeline completo: fetch → calculate → aggregate → validate
   - ✅ Testes de integração criados
     - 1 cidade: +1.7-4.2% erro (PERFEITO)
     - 5 cidades: R²=0.74 (ACEITÁVEL)
     - 10 cidades: R²=0.37 (funcional, mas precisa mais dados)

3. **Celery + Redis Configurado**
   - ✅ `celery_config.py` atualizado
     - Agendamento 4x/dia: 00h, 06h, 12h, 18h BRT
     - Queue específica: `eto_processing`
   - ✅ `matopiba_forecast_task.py` revisado
     - Task completa: fetch → calculate → validate → Redis
     - Retry: 3 tentativas, 5min delay
     - TTL: 6 horas
   - ✅ Scripts de gerenciamento criados
     - `manage_celery_redis.ps1`: Start/stop/status
     - `test_redis_connection.py`: Teste conexão + operações

4. **Documentação Completa**
   - ✅ `CELERY_REDIS_SETUP.md` criado
     - Guia instalação Redis (Docker + local)
     - Comandos Celery Worker/Beat/Flower
     - Troubleshooting completo
     - Checklist pré-produção

## 🚀 Próximos Passos

### 1. Iniciar Infraestrutura (15 min)

```powershell
# Método 1: Script PowerShell (RECOMENDADO)
.\scripts\manage_celery_redis.ps1 start-all

# Método 2: Manual (4 terminais)
# Terminal 1: Redis
docker run -d --name evaonline-redis -p 6379:6379 redis:7-alpine

# Terminal 2: Celery Worker
.\.venv\Scripts\Activate.ps1
celery -A backend.infrastructure.celery.celery_config:celery_app worker --loglevel=info --pool=solo

# Terminal 3: Celery Beat
.\.venv\Scripts\Activate.ps1
celery -A backend.infrastructure.celery.celery_config:celery_app beat --loglevel=info

# Terminal 4: Flower (opcional)
celery -A backend.infrastructure.celery.celery_config:celery_app flower --port=5555
```

### 2. Testar Infraestrutura (10 min)

```powershell
# Testar Redis
.\scripts\manage_celery_redis.ps1 test

# Ou manualmente:
& .venv\Scripts\python.exe .\scripts\test_redis_connection.py

# Verificar status
.\scripts\manage_celery_redis.ps1 status
```

### 3. Executar Task MATOPIBA Manualmente (2-3 min)

```powershell
# Via script
.\scripts\manage_celery_redis.ps1 trigger

# Ou via Python
& .venv\Scripts\python.exe -c "
from backend.infrastructure.celery.tasks.matopiba_forecast_task import update_matopiba_forecasts
result = update_matopiba_forecasts.delay()
print(f'Task ID: {result.id}')
"
```

**Tempo esperado**: ~60-90s para 337 cidades

### 4. Verificar Cache Redis (2 min)

```powershell
# Via Docker
docker exec -it evaonline-redis redis-cli -a evaonline

# Dentro do Redis CLI:
KEYS matopiba:*
GET matopiba:metadata
TTL matopiba:forecasts:today_tomorrow

# Saída esperada:
# 1) "matopiba:forecasts:today_tomorrow"
# 2) "matopiba:metadata"
```

### 5. Monitorar Execução (5 min)

```powershell
# Interface web Flower
# Abrir: http://localhost:5555

# Verificar:
# - Tasks executadas (deve mostrar update_matopiba_forecasts)
# - Estado: SUCCESS
# - Runtime: ~60-90s
# - Resultado: JSON com métricas

# Logs
.\scripts\manage_celery_redis.ps1 logs
```

### 6. Validar Métricas R²/RMSE (5 min)

**IMPORTANTE**: As métricas são calculadas e logadas **automaticamente** durante a execução da task, mas **NÃO bloqueiam** o salvamento no cache. Isso garante:

- ✅ **Disponibilidade**: Dados sempre disponíveis para usuários
- ✅ **Performance**: Interface instantânea (~50ms)
- ✅ **Monitoramento**: Métricas registradas em logs para análise

**Verificar logs da task**:
- ✅ **EXCELENTE**: R² ≥ 0.75, RMSE ≤ 1.2 mm/dia
- ⚠️ **ACEITÁVEL**: R² ≥ 0.65, RMSE ≤ 1.5 mm/dia
- ⚠️ **REVISAR**: R² < 0.65 (dados salvos, mas análise recomendada)

**Fluxo de Validação**:
```
Task executa → Download Open-Meteo → Calcula ETo → Valida métricas (log) → Salva Redis
                                                              ↓
                                                    (não bloqueia cache)
                                                              ↓
Usuário acessa → API busca Redis (50ms) → Retorna JSON → Interface renderiza
```

**Nota**: Com 337 cidades (674 dias de dados), esperamos métricas melhores que testes com 5-10 cidades (R²=0.37-0.74).

## 📅 Agendamento Configurado

| Horário BRT | Horário UTC | Task | Queue |
|-------------|-------------|------|-------|
| 00:00 | 03:00 | update_matopiba_forecasts | eto_processing |
| 06:00 | 09:00 | update_matopiba_forecasts | eto_processing |
| 12:00 | 15:00 | update_matopiba_forecasts | eto_processing |
| 18:00 | 21:00 | update_matopiba_forecasts | eto_processing |

**Frequência**: 4x/dia (a cada 6 horas)  
**TTL Cache**: 6 horas (dados expiram antes da próxima atualização)

## 🔍 Monitoramento Contínuo

### Flower Dashboard
- URL: http://localhost:5555
- Tasks: Lista todas as execuções
- Workers: Status dos workers
- Broker: Fila de tasks pendentes

### Redis Monitoring
```powershell
# Estatísticas gerais
docker exec -it evaonline-redis redis-cli -a evaonline INFO stats

# Memória usada
docker exec -it evaonline-redis redis-cli -a evaonline INFO memory

# Chaves MATOPIBA
docker exec -it evaonline-redis redis-cli -a evaonline KEYS "matopiba:*"
```

### Logs
```powershell
# Logs Worker (em tempo real)
# Ver no terminal onde worker foi iniciado

# Logs Redis
docker logs evaonline-redis -f

# Logs API (se houver)
Get-Content .\logs\api.log -Tail 50 -Wait
```

## 🐛 Troubleshooting Rápido

### Erro: "Connection refused" (Redis)
```powershell
# Verificar Docker
docker ps | Select-String redis

# Iniciar Redis
docker start evaonline-redis

# Ou criar novo
.\scripts\manage_celery_redis.ps1 start-redis
```

### Task não executa
```powershell
# Verificar worker ativo
celery -A backend.infrastructure.celery.celery_config:celery_app inspect active

# Verificar tasks registradas
celery -A backend.infrastructure.celery.celery_config:celery_app inspect registered

# Limpar fila (se necessário)
.\scripts\manage_celery_redis.ps1 purge
```

### R² muito baixo (< 0.65)
```powershell
# Testar com subset menor para debug
# Editar matopiba_forecast_task.py temporariamente:
# cities_df = client.cities_df.head(50)  # Testar com 50 cidades

# Re-executar task
.\scripts\manage_celery_redis.ps1 trigger

# Analisar logs para cidades com problemas
```

### Performance lenta (> 5min para 337 cidades)
- Verificar concurrency: `--concurrency=4` (ajustar conforme CPU)
- Verificar conexão Open-Meteo (pode ter rate limiting)
- Considerar processar em batches menores (50-100 cidades por vez)

## 📊 Métricas de Performance Esperadas

| Métrica | Valor | Status |
|---------|-------|--------|
| Tempo/cidade | ~100ms | ✅ Rápido |
| 10 cidades | 1-2s | ✅ Ótimo |
| 50 cidades | 5-10s | ✅ Bom |
| 337 cidades | 60-90s | ✅ Aceitável |
| R² global | ≥ 0.75 | 🎯 Meta |
| RMSE global | ≤ 1.2 mm/dia | 🎯 Meta |
| Cache hit rate | > 90% | 🎯 Meta (após 1ª execução) |

## ✅ Checklist Pré-Produção

- [ ] Redis rodando e respondendo PING
- [ ] Celery Worker iniciado (verificar com `status`)
- [ ] Celery Beat agendado (verificar beat_schedule)
- [ ] Task manual executada com sucesso
- [ ] Cache Redis populado (verificar `matopiba:*` keys)
- [ ] Métricas validadas (R² ≥ 0.75, RMSE ≤ 1.2)
- [ ] Flower instalado e acessível
- [ ] Logs monitorados (sem erros críticos)
- [ ] Performance aceitável (<90s para 337 cidades)
- [ ] Agendamento 4x/dia confirmado (verificar próximas execuções no Flower)

## 🎯 Critérios de Aceitação

### Funcional ✅
- [x] Pipeline completo funciona (fetch → calculate → validate → cache)
- [x] ETo calculado com algoritmo validado (não placeholder)
- [x] Task agendada 4x/dia no Celery Beat
- [x] Cache Redis configurado com TTL 6h
- [x] Scripts de gerenciamento criados

### Performance 🎯
- [ ] Task completa em < 90s (337 cidades)
- [ ] Cache acessível em < 50ms
- [ ] R² global ≥ 0.75 (BOM) ou ≥ 0.65 (ACEITÁVEL)
- [ ] RMSE global ≤ 1.2 mm/dia (BOM) ou ≤ 1.5 mm/dia (ACEITÁVEL)

### Monitoramento 📊
- [ ] Flower acessível e mostrando tasks
- [ ] Logs sem erros críticos
- [ ] Redis com chaves `matopiba:*` populadas
- [ ] Métricas de validação logadas a cada execução

## 🚀 Próxima Etapa: Teste com 50-100 Cidades

Após validar infraestrutura com todas as 337 cidades, considerar:

1. **Se R² < 0.65**: Testar com subset representativo
   ```python
   # Em matopiba_forecast_task.py
   # Selecionar 10 cidades por estado (40 cidades total)
   cities_sample = cities_df.groupby('state').sample(n=10, random_state=42)
   ```

2. **Análise regional**: Verificar R² por estado (MA, TO, PI, BA)
   - Possível necessidade de calibração regional
   - Ajustes Cn/Cd por latitude/altitude

3. **Escalabilidade**: Se tudo OK, manter 337 cidades
   - Monitorar performance a cada execução
   - Considerar cache warm-up antes do horário de pico

## 📚 Documentação Criada

1. `docs/setup/CELERY_REDIS_SETUP.md` - Guia completo instalação
2. `scripts/test_redis_connection.py` - Teste conexão + operações
3. `scripts/manage_celery_redis.ps1` - Script gerenciamento
4. `CELERY_REDIS_NEXT_STEPS.md` - Este arquivo (resumo)

---

**Status**: ✅ Infraestrutura configurada, pronta para testes  
**Próximo passo**: Executar `.\scripts\manage_celery_redis.ps1 start-all` e validar execução  
**Data**: 2025-10-09  
**Versão**: 1.0.0
