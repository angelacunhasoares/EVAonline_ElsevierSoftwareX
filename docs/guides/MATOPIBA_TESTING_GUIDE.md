# 🧪 GUIA DE TESTES - MATOPIBA Pipeline Completo

## ✅ O QUE JÁ FOI FEITO

### 1. Backend Implementado
- ✅ **OpenMeteo Client** (`backend/api/services/openmeteo_matopiba_client.py`)
  - Busca previsões para 337 cidades em lotes de 50
  - Retorna: T2M_MAX, T2M_MIN, RH2M, WS2M, ALLSKY_SFC_SW_DWN, PRECTOTCORR, ETo_OpenMeteo
  
- ✅ **Pipeline ETo** (`backend/core/eto_calculation/eto_matopiba.py`)
  - SEM data_fusion (usa apenas dados Open-Meteo)
  - preprocessing() + calculate_eto()
  - Validação: R², RMSE, Bias, MAE com status baseado em FAO-56

- ✅ **Celery Task** (`backend/infrastructure/celery/tasks/matopiba_forecast_task.py`)
  - Task `update_matopiba_forecasts`
  - Processa 337 cidades em ~27 segundos
  - Salva no Redis com TTL 6 horas
  
- ✅ **FastAPI Endpoints** (`backend/api/routes/matopiba.py`)
  - `GET /api/v1/matopiba/forecasts` - Dados completos
  - `GET /api/v1/matopiba/metadata` - Info rápida
  - `GET /api/v1/matopiba/status` - Health check
  - `POST /api/v1/matopiba/refresh` - Força atualização
  - `GET /api/v1/matopiba/task-status/{id}` - Status da task
  - `GET /api/v1/matopiba/health` - Ping

### 2. Configuração Redis Corrigida
- ✅ **Problema identificado**: Redis 6+ usa ACL, formato correto é `redis://default:password@host:port/db`
- ✅ **Corrigido em**:
  - `backend/infrastructure/celery/tasks/matopiba_forecast_task.py` (linha 44)
  - `backend/api/routes/matopiba.py` (linha 29)
- ✅ **Senha**: `evaonline`

### 3. Dados Populados no Redis
- ✅ **Executado**: `test_matopiba_task.py`
- ✅ **Resultado**: 337 cidades processadas com sucesso
- ✅ **Duração**: 27.17 segundos
- ✅ **Taxa de sucesso**: 100% (337/337)
- ✅ **Chaves Redis**:
  - `matopiba:forecasts:today_tomorrow` (pickle) - Dados completos
  - `matopiba:metadata` (JSON) - Metadata

### 4. Frontend Atualizado
- ✅ **Arquivo**: `frontend/components/matopiba_forecast_maps.py`
- ✅ **URL correta**: `/api/v1/matopiba/forecasts`
- ✅ **Tratamento de erros**: Timeout, 503, ConnectionError
- ✅ **Painel de validação**: Com referências científicas FAO-56
- ✅ **Fallback**: Mock data se API falhar

---

## ⚠️ PROBLEMA ATUAL

### Métricas de Validação Ruins
```python
{
  'r2': -10.102159199630107,      # ❌ Esperado: 0.75 a 1.0
  'rmse': 5.2804616602732,        # ❌ Esperado: < 1.5 mm/dia
  'bias': 4.483442197928448,      # ❌ Esperado: ±0.5 mm/dia
  'mae': 4.483442197928448,
  'n_samples': 674,
  'status': 'INSUFICIENTE'
}
```

**Possíveis causas**:
1. ❓ ETo calculada pela EVAonline está ~4.5 mm/dia ACIMA da Open-Meteo
2. ❓ Unidades diferentes? (mm/dia vs mm/hora?)
3. ❓ Erro no preprocessing dos dados Open-Meteo?
4. ❓ Parâmetros errados no cálculo Penman-Monteith?

**PRÓXIMO PASSO CRÍTICO**: Investigar por que a ETo EVAonline diverge tanto da ETo Open-Meteo.

---

## 🚀 COMO CONTINUAR OS TESTES

### Passo 1: Iniciar Backend FastAPI

**Opção A**: API + Dash (interface completa)
```powershell
$env:PYTHONPATH="$PWD"
.venv\Scripts\python.exe backend\main.py
```

**Opção B**: Apenas API (para testes isolados) - **RECOMENDADO**
```powershell
.venv\Scripts\python.exe start_api_only.py
```

**IMPORTANTE**: Deixe o terminal aberto! Não feche ou cancele com CTRL+C.

### Passo 2: Testar Endpoints (em OUTRO terminal)

#### 2.1 Verificar Metadata
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/matopiba/metadata" -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

**Esperado**:
```json
{
  "updated_at": "2025-10-09T13:55:22.796024",
  "next_update": "2025-10-09T19:55:22.796024",
  "n_cities": 337,
  "success_rate": 100.0,
  "version": "1.0.0"
}
```

#### 2.2 Testar Forecasts (resumido - apenas primeiras 2 cidades)
```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/matopiba/forecasts" -UseBasicParsing
$data = $response.Content | ConvertFrom-Json
Write-Host "Cidades: $($data.forecasts.Count)"
Write-Host "Validação R²: $($data.validation.r2)"
Write-Host "Validação RMSE: $($data.validation.rmse)"
Write-Host "Status: $($data.validation.status)"
```

#### 2.3 Verificar Estrutura de Dados (primeira cidade)
```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/matopiba/forecasts" -UseBasicParsing
$data = $response.Content | ConvertFrom-Json
$first_city = $data.forecasts.PSObject.Properties | Select-Object -First 1
$first_city.Value | ConvertTo-Json -Depth 5
```

### Passo 3: Testar Frontend Dash

1. **Com backend rodando**, abra navegador em: `http://localhost:8000/`

2. **Navegar para aba**: 🌾 MATOPIBA, Brasil

3. **Verificar**:
   - [ ] Seletor de variável: ETo, Precipitação
   - [ ] Seletor de dia: Hoje, Amanhã
   - [ ] Mapas renderizam (4 combinações possíveis)
   - [ ] Tooltips mostram valores ao passar mouse
   - [ ] Status bar exibe: última atualização, próxima atualização, R², RMSE
   - [ ] Painel de validação abaixo dos mapas de ETo
   - [ ] Referências científicas no rodapé (Allen et al., Popova, Paredes)

4. **Testar erro handling**:
   - Parar backend (CTRL+C)
   - Recarregar página
   - Deve mostrar alerta: "⚠️ Backend Offline"

---

## 🔍 INVESTIGAÇÃO: Por que R² = -10.1?

### Script de Análise

Crie um script `debug_eto_validation.py`:

```python
import pickle
import redis
import pandas as pd
from sklearn.metrics import r2_score
import numpy as np

# Conectar Redis
redis_client = redis.from_url("redis://default:evaonline@localhost:6379/0")

# Buscar dados
forecasts_raw = redis_client.get("matopiba:forecasts:today_tomorrow")
cache_data = pickle.loads(forecasts_raw)

# Extrair forecasts
forecasts_dict = cache_data['forecasts']

# Coletar todos os valores de ETo
all_eto_eva = []
all_eto_om = []

for city_code, city_data in forecasts_dict.items():
    forecast = city_data['forecast']
    for date, values in forecast.items():
        eto_eva = values.get('ETo_EVAonline')
        eto_om = values.get('ETo_OpenMeteo')
        
        if eto_eva is not None and eto_om is not None:
            all_eto_eva.append(eto_eva)
            all_eto_om.append(eto_om)

# Converter para arrays
all_eto_eva = np.array(all_eto_eva)
all_eto_om = np.array(all_eto_om)

print(f"\n{'='*70}")
print("ANÁLISE DE VALIDAÇÃO ETo")
print(f"{'='*70}\n")

print(f"Total amostras: {len(all_eto_eva)}\n")

print("ETo EVAonline:")
print(f"  Min:     {all_eto_eva.min():.3f} mm/dia")
print(f"  Max:     {all_eto_eva.max():.3f} mm/dia")
print(f"  Média:   {all_eto_eva.mean():.3f} mm/dia")
print(f"  Mediana: {np.median(all_eto_eva):.3f} mm/dia\n")

print("ETo Open-Meteo:")
print(f"  Min:     {all_eto_om.min():.3f} mm/dia")
print(f"  Max:     {all_eto_om.max():.3f} mm/dia")
print(f"  Média:   {all_eto_om.mean():.3f} mm/dia")
print(f"  Mediana: {np.median(all_eto_om):.3f} mm/dia\n")

print("Diferença (EVAonline - Open-Meteo):")
diff = all_eto_eva - all_eto_om
print(f"  Min:     {diff.min():.3f} mm/dia")
print(f"  Max:     {diff.max():.3f} mm/dia")
print(f"  Média:   {diff.mean():.3f} mm/dia (BIAS)")
print(f"  Mediana: {np.median(diff):.3f} mm/dia\n")

# Recalcular R²
r2 = r2_score(all_eto_om, all_eto_eva)
print(f"R² recalculado: {r2:.3f}")

# Mostrar primeiros 10 valores
print(f"\nPrimeiros 10 pares de valores:")
print(f"{'EVAonline':<12} {'OpenMeteo':<12} {'Diferença'}")
print(f"{'-'*40}")
for i in range(min(10, len(all_eto_eva))):
    print(f"{all_eto_eva[i]:>10.2f}   {all_eto_om[i]:>10.2f}   {(all_eto_eva[i]-all_eto_om[i]):>10.2f}")
```

**Execute**:
```powershell
.venv\Scripts\python.exe debug_eto_validation.py
```

**Analisar**:
- Se ETo EVAonline >> ETo OpenMeteo → problema no cálculo ou unidades
- Se valores parecem aleatórios → problema na correspondência de datas/cidades
- Se diferença sistemática → verificar parâmetros (latitude, altitude, etc.)

---

## 📋 PRÓXIMOS PASSOS

### Curto Prazo (hoje)
1. ✅ Iniciar backend e manter rodando
2. ⏳ Testar endpoints API
3. ⏳ Executar script de debug para entender R² negativo
4. ⏳ Testar frontend com dados reais

### Médio Prazo
1. 🔧 Corrigir cálculo de ETo ou identificar origem da divergência
2. ✅ Validar métricas (target: R² > 0.75, RMSE < 1.5 mm/dia)
3. ⏳ Configurar Celery Beat para atualização automática a cada 6h

### Longo Prazo
1. Documentar decisões sobre validação
2. Adicionar testes unitários para `eto_matopiba.py`
3. Monitorar performance (tempo de execução, uso de memória)

---

## 📞 SUPORTE

### Logs Importantes
- **API**: `logs/api.log`
- **Task Celery**: logs no terminal onde a task foi executada
- **Redis**: `docker logs evaonline-redis-test`

### Comandos Úteis

**Verificar Redis**:
```powershell
docker exec evaonline-redis-test redis-cli -a evaonline KEYS "matopiba:*"
docker exec evaonline-redis-test redis-cli -a evaonline TTL "matopiba:metadata"
```

**Limpar cache Redis (forçar nova busca)**:
```powershell
docker exec evaonline-redis-test redis-cli -a evaonline DEL "matopiba:forecasts:today_tomorrow"
docker exec evaonline-redis-test redis-cli -a evaonline DEL "matopiba:metadata"
```

**Reexecutar task manualmente**:
```powershell
.venv\Scripts\python.exe test_matopiba_task.py
```

---

**Última atualização**: 2025-10-09 14:15  
**Status**: ✅ Backend implementado | ⚠️ Validação precisa investigação | ⏳ Testes pendentes
