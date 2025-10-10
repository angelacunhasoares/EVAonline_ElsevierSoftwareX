# 🌾 Arquitetura MATOPIBA - Previsões Meteorológicas

## 📋 Visão Geral

Sistema de visualização de previsões meteorológicas para as 337 cidades da região MATOPIBA (Maranhão, Tocantins, Piauí, Bahia), com atualização automática via cache e conformidade com licença CC-BY-NC.

---

## 🎯 Características Principais

### **1. Interface Interativa**
- ✅ Checkboxes para seleção de variáveis (ETo, Precipitação, etc)
- ✅ Seleção de dias (Hoje/Amanhã) com datas automáticas
- ✅ Grid dinâmico e responsivo (1-10 mapas simultâneos)
- ✅ Sem parâmetros de data manual (evita requisições desnecessárias)

### **2. Performance**
- ✅ Cache Redis (TTL 6 horas)
- ✅ Resposta instantânea (< 100ms)
- ✅ Atualização automática em background (Celery)
- ✅ Suporta tráfego ilimitado de usuários

### **3. Conformidade de Licença**
- ✅ Apenas visualização (CC-BY-NC permitido)
- ✅ Download bloqueado
- ✅ Atribuição obrigatória exibida
- ✅ Aviso de uso não-comercial

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                  FLUXO DE DADOS MATOPIBA                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ⏰ Celery Beat Scheduler                                   │
│     └─> Agenda: 00:00, 06:00, 12:00, 18:00 (a cada 6h)    │
│                                                              │
│  🔄 Celery Worker Task                                      │
│     └─> update_matopiba_forecasts()                        │
│         ├─> Carrega 337 cidades (CITIES_MATOPIBA_337.csv)  │
│         ├─> Busca Open-Meteo em lotes de 50 cidades        │
│         │   (337 cidades / 50 = ~7 lotes)                  │
│         ├─> Duração: 5-7 minutos (com rate limiting)       │
│         └─> Salva no Redis (TTL 6h)                        │
│                                                              │
│  💾 Redis Cache                                             │
│     └─> Key: "matopiba:forecasts:today_tomorrow"           │
│     └─> Estrutura: {                                       │
│           "data": {                                        │
│             "city_code_1": {                               │
│               "city_name": "Abreulândia",                  │
│               "latitude": -9.62,                           │
│               "longitude": -49.16,                         │
│               "today": {                                   │
│                 "date": "2025-10-09",                      │
│                 "temp_max": 35.2,                          │
│                 "temp_min": 22.1,                          │
│                 "precipitation": 0.0,                      │
│                 "eto_openmeteo": 6.8,                      │
│                 "radiation": 24.5,                         │
│                 "wind_speed": 3.2,                         │
│                 "humidity_max": 85,                        │
│                 "humidity_min": 45                         │
│               },                                           │
│               "tomorrow": { ... }                          │
│             },                                             │
│             "city_code_2": { ... },                        │
│             ...337 cidades                                 │
│           },                                               │
│           "updated_at": "2025-10-09T06:00:00",            │
│           "next_update": "2025-10-09T12:00:00"            │
│         }                                                  │
│     └─> TTL: 21,600 segundos (6 horas)                    │
│                                                              │
│  🚀 FastAPI Endpoint                                        │
│     └─> GET /api/matopiba/forecasts                       │
│         ├─> Lê do Redis (< 50ms)                          │
│         ├─> ZERO chamadas ao Open-Meteo                   │
│         └─> Retorna JSON com 337 cidades                  │
│                                                              │
│  🎨 Frontend Dash                                           │
│     └─> Página: /matopiba-forecast                        │
│         ├─> Checkboxes de variáveis                       │
│         ├─> Checkboxes de dias (Hoje/Amanhã)              │
│         ├─> Gera mapas dinamicamente                      │
│         ├─> Auto-refresh a cada 5 min (verifica cache)    │
│         └─> Renderização instantânea                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Variáveis Disponíveis

### **Grupo: Água e Evapotranspiração**
| Variável | Unidade | Fonte | Descrição |
|----------|---------|-------|-----------|
| ETo Calculado | mm/dia | EVAonline | Penman-Monteith (Calculado) |
| ETo Open-Meteo | mm/dia | Open-Meteo | FAO-56 (Referência) |
| Precipitação | mm | Open-Meteo | Acumulada diária |
| Déficit Hídrico | mm | Calculado | ETo - Precipitação |

### **Grupo: Temperatura**
| Variável | Unidade | Fonte | Descrição |
|----------|---------|-------|-----------|
| Temp. Máxima | °C | Open-Meteo | Máxima do dia |
| Temp. Mínima | °C | Open-Meteo | Mínima do dia |

### **Grupo: Outros Fatores Climáticos**
| Variável | Unidade | Fonte | Descrição |
|----------|---------|-------|-----------|
| Radiação Solar | MJ/m² | Open-Meteo | Total diário |
| Velocidade do Vento | m/s | Open-Meteo | Máxima do dia |
| Umidade Relativa | % | Open-Meteo | Média diária |

---

## 🔢 Análise de Requisições

### **Consumo Diário**
```
Cenário Base:
- 337 cidades MATOPIBA
- 1 requisição por cidade (retorna hoje + amanhã)
- 4 atualizações/dia (a cada 6h)
- Total: 337 × 4 = 1,348 requisições/dia

Limite Open-Meteo (Free Tier):
- 10,000 requisições/dia
- Utilização: 13.5% 
- Margem de segurança: 86.5% ✅

Usuários Simultâneos:
- 1 usuário = 0 requisições adicionais (usa cache)
- 1,000 usuários = 0 requisições adicionais
- 10,000 usuários = 0 requisições adicionais ✅
```

### **Horários de Atualização**
```python
HORARIOS_ATUALIZACAO = [
    "00:00",  # Meia-noite (preparar dia)
    "06:00",  # Manhã (usuários começam a acessar)
    "12:00",  # Meio-dia (previsões mais precisas)
    "18:00",  # Tarde (preparar amanhã)
]

# Configurado via Celery Beat
CELERY_BEAT_SCHEDULE = {
    'update-matopiba-forecasts': {
        'task': 'matopiba.update_forecasts',
        'schedule': crontab(hour='*/6', minute=0),
    },
}
```

---

## 🎨 Interface do Usuário

### **Layout Responsivo**

```
Seleção de 1 variável × 2 dias (2 mapas):
┌─────────────────────┐  ┌─────────────────────┐
│ ETo - Hoje          │  │ ETo - Amanhã        │
│ (09/10/2025)        │  │ (10/10/2025)        │
└─────────────────────┘  └─────────────────────┘

Seleção de 2 variáveis × 2 dias (4 mapas):
┌─────────────────────┐  ┌─────────────────────┐
│ ETo - Hoje          │  │ ETo - Amanhã        │
└─────────────────────┘  └─────────────────────┘
┌─────────────────────┐  ┌─────────────────────┐
│ Precipitação - Hoje │  │ Precipitação - Amanhã│
└─────────────────────┘  └─────────────────────┘

Seleção de 3+ variáveis (Grid 3 colunas):
┌────────────┐  ┌────────────┐  ┌────────────┐
│ Var1-Hoje  │  │ Var1-Amanhã│  │ Var2-Hoje  │
└────────────┘  └────────────┘  └────────────┘
┌────────────┐  ┌────────────┐  ┌────────────┐
│ Var2-Amanhã│  │ Var3-Hoje  │  │ Var3-Amanhã│
└────────────┘  └────────────┘  └────────────┘
```

### **Limites de Seleção**
```python
MAX_MAPAS = 10  # Máximo de mapas simultâneos

# Exemplos válidos:
✅ 2 variáveis × 2 dias = 4 mapas
✅ 5 variáveis × 2 dias = 10 mapas
✅ 7 variáveis × 1 dia = 7 mapas

# Exemplos inválidos:
❌ 6 variáveis × 2 dias = 12 mapas (excede limite)
❌ 11 variáveis × 1 dia = 11 mapas (excede limite)
```

---

## 🔐 Conformidade de Licença CC-BY-NC

### **O que é PERMITIDO:**
✅ Visualização dos mapas na interface web
✅ Comparação entre variáveis e dias
✅ Screenshot dos mapas para uso pessoal
✅ Análise visual dos padrões climáticos

### **O que é PROIBIDO:**
❌ Download dos dados brutos
❌ Exportação de CSV/JSON
❌ API pública dos dados
❌ Uso comercial (revenda, consultoria paga)
❌ Redistribuição dos dados

### **Atribuição Obrigatória:**
```html
📊 Dados fornecidos por Open-Meteo (CC-BY-NC 4.0)
⚠️ Apenas para visualização - Uso não-comercial
```

---

## 📁 Estrutura de Arquivos

```
backend/
├── api/
│   ├── routes/
│   │   └── matopiba.py           # Endpoint FastAPI
│   └── services/
│       └── openmeteo_client.py   # Cliente Open-Meteo
├── infrastructure/
│   └── celery/
│       └── tasks/
│           └── matopiba_tasks.py # Task de atualização

frontend/
└── pages/
    └── matopiba_forecast.py      # Interface Dash

data/
└── csv/
    └── CITIES_MATOPIBA_337.csv   # 337 cidades

docs/
└── MATOPIBA_ARCHITECTURE.md      # Este arquivo
```

---

## 🚀 Implementação

### **Fase 1: Backend (API + Cache)**
1. ✅ Criar `openmeteo_client.py`
2. ✅ Criar `matopiba_tasks.py` (Celery)
3. ✅ Criar endpoint `/api/matopiba/forecasts`
4. ✅ Configurar Celery Beat schedule
5. ✅ Testar atualização automática

### **Fase 2: Frontend (Interface)**
6. ✅ Criar `matopiba_forecast.py` (página Dash)
7. ✅ Implementar seleção de variáveis (checkboxes)
8. ✅ Implementar seleção de dias (checkboxes)
9. ✅ Criar função de renderização de mapas
10. ✅ Adicionar atribuição CC-BY-NC

### **Fase 3: Otimizações**
11. ⏳ Calcular ETo EVAonline (Penman-Monteith)
12. ⏳ Adicionar estatísticas por estado
13. ⏳ Implementar comparação lado a lado
14. ⏳ Adicionar export de imagens PNG

---

## 🧪 Testes

### **Teste 1: Atualização Automática**
```bash
# Executar task manualmente
celery -A backend.infrastructure.celery.celery_app call \
    matopiba.update_forecasts

# Verificar cache Redis
redis-cli GET "matopiba:forecasts:today_tomorrow"
```

### **Teste 2: Carga da Interface**
```python
# Acessar página
http://localhost:8050/matopiba-forecast

# Selecionar:
✅ ETo Calculado
✅ Precipitação
✅ Hoje
✅ Amanhã

# Resultado esperado: 4 mapas renderizados < 2 segundos
```

### **Teste 3: Limite de Requisições**
```python
# Simular 1000 usuários acessando simultaneamente
import asyncio
import httpx

async def test_concurrent_users():
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get("http://localhost:8000/api/matopiba/forecasts")
            for _ in range(1000)
        ]
        responses = await asyncio.gather(*tasks)
        
        # Todos devem retornar 200 OK
        assert all(r.status_code == 200 for r in responses)
        
        # Todos devem ter cache_status = "hit"
        assert all(r.json()["metadata"]["cache_status"] == "hit" 
                   for r in responses)

# Requisições ao Open-Meteo: 0 ✅
```

---

## 📊 Monitoramento

### **Métricas Chave**
```python
# Celery Task
- Duração da atualização (target: < 7 minutos)
- Taxa de sucesso (target: > 99%)
- Cidades processadas (target: 337)

# Redis Cache
- Hit rate (target: > 99%)
- TTL restante
- Tamanho do cache (~2-3 MB)

# Frontend
- Tempo de renderização (target: < 2s)
- Mapas gerados por sessão
- Variáveis mais selecionadas
```

### **Alertas**
```python
# Celery Beat
if task_duration > 10 minutes:
    alert("Atualização MATOPIBA muito lenta")

if success_rate < 95%:
    alert("Alta taxa de falha na atualização")

# Redis
if cache_miss_rate > 5%:
    alert("Cache MATOPIBA degradado")

# Open-Meteo API
if daily_requests > 8000:
    alert("Aproximando do limite de requisições")
```

---

## 🔄 Melhorias Futuras

### **Curto Prazo**
- [ ] Adicionar gráficos de série temporal (7 dias)
- [ ] Implementar modo escuro
- [ ] Adicionar tooltips informativos
- [ ] Criar tour guiado (primeira visita)

### **Médio Prazo**
- [ ] Calcular ETo EVAonline (Penman-Monteith) para comparação
- [ ] Adicionar análise comparativa (hoje vs amanhã)
- [ ] Implementar alertas de eventos extremos
- [ ] Criar dashboard de resumo por estado

### **Longo Prazo**
- [ ] Histórico de previsões (7 dias anteriores)
- [ ] Machine Learning para correção de bias
- [ ] API pública com dados processados (licença própria)
- [ ] Integração com Xavier dataset

---

## 📚 Referências

- Open-Meteo API: https://open-meteo.com/
- Licença CC-BY-NC 4.0: https://creativecommons.org/licenses/by-nc/4.0/
- MATOPIBA: https://www.embrapa.br/tema-matopiba
- Celery Beat: https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html
- Redis Caching: https://redis.io/docs/manual/client-side-caching/

---

**Atualizado:** 09/10/2025  
**Versão:** 1.0  
**Autor:** EVAonline Team
