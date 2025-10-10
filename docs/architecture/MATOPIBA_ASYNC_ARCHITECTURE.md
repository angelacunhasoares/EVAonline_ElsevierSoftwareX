# 🏗️ Arquitetura: EVAonline MATOPIBA - Cache-First Async

## 📐 Diagrama de Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENDAMENTO CELERY BEAT                          │
│                    4x por dia: 00h, 06h, 12h, 18h BRT               │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    TASK: update_matopiba_forecasts                  │
│                         (executa em background)                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
┌───────────────────────┐   ┌───────────────────────┐
│  STEP 1: Fetch Data   │   │   Duração: ~30-40s    │
│  Open-Meteo API       │   │   (337 cidades)       │
│  - Hourly forecast    │   └───────────────────────┘
│  - 2 dias (today+1)   │
│  - 12 variáveis       │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐   ┌───────────────────────┐
│  STEP 2: Calculate    │   │   Duração: ~20-30s    │
│  ETo EVAonline        │   │   (algoritmo R²=0.83) │
│  - eto_hourly.py      │   └───────────────────────┘
│  - Penman-Monteith    │
│  - Nighttime fix      │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐   ┌───────────────────────┐
│  STEP 3: Validate     │   │   NÃO BLOQUEIA!       │
│  Métricas R²/RMSE     │   │   Apenas LOG          │
│  - R² ≥ 0.75 ✅       │   └───────────────────────┘
│  - RMSE ≤ 1.2 ✅      │
│  - Log warnings ⚠️    │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐   ┌───────────────────────┐
│  STEP 4: Save Redis   │   │   Duração: ~1-2s      │
│  - forecasts (pickle) │   │   TTL: 6 horas        │
│  - metadata (JSON)    │   └───────────────────────┘
│  - TTL: 6h            │
└──────────┬────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          REDIS CACHE                                │
│  Key: matopiba:forecasts:today_tomorrow                             │
│  - 337 cidades × 2 dias × 2 ETo (EVAonline + OpenMeteo)            │
│  - Validation metrics: R², RMSE, Bias, MAE, Status                 │
│  - Metadata: timestamp, next_update, version                       │
│  - Size: ~500KB-1MB (pickle compressed)                            │
│  - TTL: 6 horas (expira antes da próxima atualização)              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ (usuário acessa interface)
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       FRONTEND REQUEST                              │
│  GET /api/v1/matopiba/forecasts                                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       BACKEND API                                   │
│  1. Verifica Redis cache                                           │
│  2. Se existe: retorna imediatamente (~50ms) ✅                    │
│  3. Se não existe: retorna erro 503 (aguardar próxima task) ⚠️     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       FRONTEND MAP                                  │
│  - Renderiza mapa MATOPIBA                                         │
│  - Popula marcadores com ETo_EVAonline                             │
│  - Mostra comparação ETo_EVAonline vs ETo_OpenMeteo                │
│  - Exibe metadata (última atualização, próxima em X horas)         │
│  - Performance: Instantâneo! (~50ms total)                         │
└─────────────────────────────────────────────────────────────────────┘
```

## 🎯 Vantagens da Arquitetura Cache-First

### ✅ Performance
- **Interface**: 50ms (busca Redis)
- **vs Cálculo em tempo real**: 60-90s (inviável!)
- **Escalabilidade**: Suporta 1000+ usuários simultâneos

### ✅ Disponibilidade
- **Dados sempre prontos**: Atualizados 4x/dia
- **Sem loading**: Usuário não espera cálculos
- **Graceful degradation**: Se Open-Meteo cair, cache mantém dados antigos

### ✅ Qualidade
- **Validação automática**: R²/RMSE logados a cada execução
- **Não bloqueia**: Métricas ruins não impedem cache
- **Monitoramento**: Logs permitem análise pós-deploy

### ✅ Manutenibilidade
- **Erros em background**: Não afetam experiência do usuário
- **Retry automático**: Celery tenta 3× antes de falhar
- **Logs detalhados**: Troubleshooting facilitado

## 📊 Comparação: Síncrono vs Assíncrono

| Aspecto | Síncrono (ruim) | Assíncrono (ótimo) |
|---------|-----------------|---------------------|
| **Tempo resposta** | 60-90s ❌ | 50ms ✅ |
| **Usuários simultâneos** | ~10 ❌ | 1000+ ✅ |
| **Falha Open-Meteo** | Erro 500 ❌ | Cache antigo ⚠️ |
| **Validação R²/RMSE** | Bloqueia ❌ | Background ✅ |
| **Custo servidor** | Alto ❌ | Baixo ✅ |

## 🔄 Fluxo de Atualização (Exemplo Real)

### 00:00 BRT - Primeira Execução do Dia
```
00:00:00 → Task inicia
00:00:02 → Fetch Open-Meteo (337 cidades)
00:00:35 → Download completo (12 variáveis × 48h × 337 = ~200k pontos)
00:00:36 → Calcula ETo EVAonline (eto_hourly.py)
00:01:05 → Cálculo completo (337 cidades × 48h)
00:01:06 → Valida métricas: R²=0.78, RMSE=1.15, Status=BOM ✅
00:01:07 → Salva Redis (TTL: 6h, expira 06:00)
00:01:08 → Task completa (duração: 68s)

LOG:
[00:01:06] INFO: ✅ QUALIDADE: EXCELENTE (R²≥0.75, RMSE≤1.2)
[00:01:07] INFO: ✅ Dados salvos no Redis (TTL: 6h)
[00:01:08] INFO: ✅ Task concluída: 337/337 cidades (100%)
```

### 00:05 BRT - Usuário Acessa Mapa
```
00:05:23 → GET /api/v1/matopiba/forecasts
00:05:23 → Redis hit! (cache válido até 06:00)
00:05:23 → Retorna JSON (500KB)
00:05:23 → Resposta total: 47ms ✅

Frontend:
- Renderiza 337 marcadores
- Mostra "Última atualização: 00:01 (há 4 minutos)"
- Mostra "Próxima atualização: 06:00 (em 5h 55min)"
```

### 06:00 BRT - Segunda Execução
```
06:00:00 → Task inicia (cache anterior expira)
06:00:35 → Download completo
06:01:05 → Cálculo completo
06:01:06 → Valida: R²=0.82, RMSE=1.08, Status=EXCELENTE ✅
06:01:07 → Atualiza Redis (novo TTL: 6h, expira 12:00)
06:01:08 → Task completa

LOG:
[06:01:06] INFO: ✅ QUALIDADE: EXCELENTE (R²≥0.75, RMSE≤1.2)
[06:01:06] INFO: 📊 Melhoria: R² +0.04, RMSE -0.07 (vs última execução)
```

### 06:30 BRT - Outro Usuário Acessa
```
06:30:12 → GET /api/v1/matopiba/forecasts
06:30:12 → Redis hit! (cache atualizado às 06:01)
06:30:12 → Retorna JSON (dados frescos)
06:30:12 → Resposta: 51ms ✅

Frontend:
- Mostra "Última atualização: 06:01 (há 29 minutos)"
- Mostra "Próxima atualização: 12:00 (em 5h 30min)"
```

## ⚠️ Cenários de Exceção

### Cenário 1: Open-Meteo indisponível
```
12:00:00 → Task inicia
12:00:02 → Fetch Open-Meteo → ConnectionTimeout ❌
12:05:02 → Retry 1/3 (após 5min)
12:10:02 → Retry 2/3 (após 5min)
12:15:02 → Retry 3/3 (após 5min)
12:20:02 → Task FALHA (após 3 tentativas)

Redis:
- Cache antigo (das 06:00) AINDA VÁLIDO até 12:00 ✅
- Usuários continuam acessando dados das 06:00
- TTL renovado automaticamente? NÃO ❌

Solução:
- Próxima task (18:00) tentará novamente
- Se Open-Meteo voltar, cache será atualizado
- Monitoramento alerta equipe se 2+ falhas consecutivas
```

### Cenário 2: Validação ruim (R² < 0.65)
```
18:00:00 → Task inicia
18:01:05 → Cálculo completo
18:01:06 → Valida: R²=0.58, RMSE=1.85, Status=INSUFICIENTE ⚠️
18:01:07 → Salva Redis MESMO ASSIM ✅ (disponibilidade > perfeição)
18:01:08 → Task completa com WARNING

LOG:
[18:01:06] WARNING: ⚠️ QUALIDADE: ABAIXO DO ESPERADO (revisar pós-deploy)
[18:01:06] WARNING:    Dados serão salvos no cache para disponibilidade
[18:01:06] WARNING:    Análise detalhada recomendada nos logs
[18:01:07] INFO: ✅ Dados salvos no Redis (com warning de qualidade)

Ação:
- Equipe recebe alerta
- Análise logs para identificar cidades problemáticas
- Possível ajuste regional (Cn/Cd por estado)
- Usuários CONTINUAM acessando (dados disponíveis)
```

### Cenário 3: Cache expirado + Task falhando
```
00:00:00 → Task falha (Open-Meteo indisponível)
06:00:00 → Task falha (Open-Meteo ainda indisponível)
06:00:01 → Cache das 18:00 (dia anterior) EXPIRA ❌

Usuário acessa:
06:05:00 → GET /api/v1/matopiba/forecasts
06:05:00 → Redis miss (cache expirado)
06:05:00 → API retorna 503 Service Unavailable
06:05:00 → Frontend mostra: "Dados temporariamente indisponíveis. Próxima tentativa: 12:00"

Solução:
- Aumentar TTL para 12h (2 ciclos) para maior resiliência?
- Implementar fallback para dados históricos (D-1)?
- Monitoramento proativo (alerta se 2 falhas consecutivas)
```

## 🎯 Decisões de Design

### Por que NÃO bloquear cache com validação?

#### ❌ Abordagem Ruim (bloqueia)
```python
if r2 < 0.65:
    logger.error("Validação falhou, NÃO salvando cache")
    raise Exception("R² insuficiente")
    # Usuário NÃO terá dados!
```

#### ✅ Abordagem Boa (não bloqueia)
```python
if r2 < 0.65:
    logger.warning("Validação abaixo do esperado, mas salvando cache")
    # Dados disponíveis, mas com warning nos logs
redis_client.setex(key, ttl, data)  # SEMPRE salva
```

**Justificativa**:
- **Disponibilidade > Perfeição**: Melhor dados com R²=0.58 que nenhum dado
- **Contexto MATOPIBA**: Região heterogênea, esperado variação regional
- **Monitoramento**: Logs permitem análise sem bloquear usuário
- **Iteração**: Permite identificar problemas em produção e ajustar

### Por que TTL = 6 horas (não 12h ou 24h)?

#### ✅ TTL = 6h (atual)
- **Sincronia perfeita**: Expira quando nova task executa
- **Dados frescos**: 4 atualizações/dia
- **Risco médio**: Se 1 task falhar, cache expira em 6h

#### ⚠️ TTL = 12h (alternativa)
- **Mais resiliente**: Sobrevive a 1 falha
- **Dados menos frescos**: Pode ter dados de 12h atrás
- **Sincronia complexa**: Pode ter cache antigo coexistindo

#### ❌ TTL = 24h (não recomendado)
- **Muito antigo**: Previsão de 24h atrás é irrelevante
- **Desperdício**: Cache gigante para dados que serão descartados

**Decisão**: Manter 6h, monitorar falhas proativamente.

## 📚 Referências

- **Cache-First Pattern**: https://web.dev/offline-cookbook/
- **Celery Best Practices**: https://docs.celeryproject.org/en/stable/userguide/tasks.html#retrying
- **Redis TTL Strategy**: https://redis.io/commands/expire

---

**Autor**: EVAonline Team  
**Data**: 2025-10-09  
**Versão**: 1.0.0
