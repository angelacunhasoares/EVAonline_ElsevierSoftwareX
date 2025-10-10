# 🔄 Análise Corrigida: Limitações das APIs

## ⚠️ DESCOBERTA CRÍTICA

### **MET Norway e NWS são APIs de PREVISÃO apenas!**

| API | Tipo de Dados | Resolução | Período |
|-----|---------------|-----------|---------|
| **NASA POWER** | Histórico + Near-real-time | Diário | 1981 - ontem |
| **MET Norway** | ⚠️ **Previsão apenas** | Horário | Hoje + 10 dias |
| **NWS/NOAA** | ⚠️ **Previsão apenas** | Horário | Hoje + 7 dias |
| **Open-Meteo** | Histórico + Previsão | Horário | 1940 - futuro |

---

## 🎯 Implicações para o Sistema

### **Problema Identificado**

O EVAonline ETo Calculator precisa de **dados históricos** (7-15 dias no passado) para:
1. Calcular ETo FAO-56 (período mínimo 7 dias)
2. Validar com dataset Xavier (1980-2013)
3. Análises retrospectivas

**MET Norway e NWS só fornecem previsão** → **Não servem para análises históricas!**

### **Casos de Uso Corretos**

| Fonte | Caso de Uso | Período Suportado |
|-------|-------------|-------------------|
| **NASA POWER** | ✅ Análise histórica<br>✅ Validação Xavier<br>✅ ETo passado | 1981 - ontem |
| **MET Norway** | ✅ Previsão ETo Europa<br>❌ Análise histórica | Hoje + 10 dias |
| **NWS** | ✅ Previsão ETo USA<br>❌ Análise histórica | Hoje + 7 dias |
| **Open-Meteo** | ⚠️ Ambos (mas CC-BY-NC)<br>✅ Histórico MATOPIBA<br>✅ Previsão global | 1940 - futuro |

---

## 📊 Estratégia de Fusão Corrigida

### **Cenário 1: Análise Histórica (7-15 dias passados)**
```
Período: 2024-09-25 a 2024-10-05 (histórico)

✅ Usar APENAS NASA POWER (global, histórico)
❌ MET Norway: Não aplicável (só previsão)
❌ NWS: Não aplicável (só previsão)
⚠️ Open-Meteo: Bloqueado (CC-BY-NC, não comercial)

Conclusão: Fonte única (NASA POWER), sem fusão
```

### **Cenário 2: Previsão de ETo (próximos 7 dias)**
```
Período: 2024-10-10 a 2024-10-17 (futuro)

Europa (Paris):
✅ NASA POWER: Dados near-real-time até ontem
✅ MET Norway: Previsão 10 dias (hoje + futuro)
→ FUSÃO VÁLIDA: NASA (baseline) + MET (refinamento)

USA (Nova York):
✅ NASA POWER: Baseline
✅ NWS: Previsão 7 dias
→ FUSÃO VÁLIDA: NASA (baseline) + NWS (refinamento)

Brasil (Balsas):
✅ NASA POWER: Dados globais
❌ MET Norway: Fora de cobertura
❌ NWS: Fora de cobertura
→ Fonte única (NASA POWER)
```

### **Cenário 3: Período Misto (passado + futuro)**
```
Período: 2024-10-05 a 2024-10-15 (5 dias passados + 5 dias futuros)

Solução:
1. Passado (05-09): NASA POWER (histórico)
2. Futuro (10-15): NASA POWER + MET Norway/NWS (fusão)
3. Juntar os períodos
```

---

## 🔧 Correções Necessárias

### **1. Remover Pré-processamento Hourly → Daily para MET/NWS**

**ANTES (incorreto):**
```python
# source_preprocessors.py
def preprocess_met_norway(df):
    # Agregar hourly → daily
    daily_df = df.groupby('date').agg({...})
```

**DEPOIS (correto):**
```python
# MET/NWS retornam previsão horária
# Para ETo, agregar internamente APENAS se necessário
# Mas manter consciência: são dados de PREVISÃO, não históricos

def preprocess_forecast_source(df, source_name):
    """
    Processa dados de previsão (MET/NWS).
    
    Nota: Dados são de PREVISÃO, não históricos.
    Agregar para resolução diária apenas se ETo requerer.
    """
    warnings = []
    warnings.append(
        f"{source_name}: Using FORECAST data (not historical). "
        f"Results represent predicted ETo, not observed."
    )
    
    # Agregação hourly → daily para ETo FAO-56
    daily_df = aggregate_hourly_to_daily(df)
    
    return daily_df, warnings
```

### **2. Validar Tipo de Período em `data_download.py`**

```python
def download_weather_data(
    data_source: Union[str, List[str]],
    data_inicial: str,
    data_final: str,
    longitude: float,
    latitude: float,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Download com validação de período (histórico vs previsão).
    """
    warnings = []
    
    # Determinar tipo de período
    today = datetime.now().date()
    start_date = datetime.strptime(data_inicial, '%Y-%m-%d').date()
    end_date = datetime.strptime(data_final, '%Y-%m-%d').date()
    
    is_historical = end_date < today
    is_forecast = start_date >= today
    is_mixed = start_date < today <= end_date
    
    # Validar compatibilidade fonte vs período
    forecast_only_sources = ['met_norway', 'nws_usa']
    
    if is_historical:
        # Período completamente no passado
        for source in data_source:
            if source in forecast_only_sources:
                warnings.append(
                    f"⚠️ {source}: Cannot provide historical data. "
                    f"This source only provides forecasts. "
                    f"Using NASA POWER for historical period instead."
                )
                # Remover fonte incompatível
                data_source = [s for s in data_source if s not in forecast_only_sources]
    
    elif is_forecast:
        # Período completamente no futuro
        logger.info("Forecast period detected, using prediction sources")
    
    elif is_mixed:
        # Período misto: dividir em histórico + previsão
        warnings.append(
            f"📅 Mixed period detected: historical ({data_inicial} to "
            f"{today - timedelta(days=1)}) + forecast ({today} to {data_final})"
        )
        
        # Estratégia: baixar em 2 etapas
        # 1. Histórico: NASA POWER
        # 2. Previsão: NASA + MET/NWS (fusão)
        # 3. Concatenar
    
    # Continue com download...
```

### **3. Atualizar `data_fusion.py` - Validação de Período**

```python
@shared_task(bind=True, name='src.data_fusion.data_fusion')
def data_fusion(
    self,
    dfs: List[dict],
    ensemble_size: int = 50,
    inflation_factor: float = 1.02,
    source_names: Optional[List[str]] = None,
    period_type: Optional[str] = None  # NOVO: 'historical', 'forecast', 'mixed'
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Fusão de dados com validação de tipo de período.
    """
    warnings = []
    
    # Validação de conformidade de licença (existente)
    # ...
    
    # NOVA VALIDAÇÃO: Tipo de período
    if period_type == 'historical':
        # Período histórico: fontes de previsão não fazem sentido
        forecast_sources = ['met_norway', 'nws_usa']
        problematic = [s for s in source_names if s in forecast_sources]
        
        if problematic:
            error_msg = (
                f"⚠️ PERIOD MISMATCH: {', '.join(problematic)} only provide "
                f"FORECAST data, but historical period was requested. "
                f"Cannot fuse forecast with historical data. "
                f"Use NASA POWER for historical analysis."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    elif period_type == 'forecast':
        # Período de previsão: OK para fusão com fontes de previsão
        logger.info("Forecast period: fusing prediction sources")
        warnings.append(
            "⚠️ Forecast period: Results represent PREDICTED ETo, "
            "not observed values."
        )
    
    # Continue com fusão Kalman Ensemble...
```

---

## 📝 Resumo das Mudanças

### **Premissas Incorretas (antes):**
- ❌ MET Norway fornece dados históricos
- ❌ NWS fornece dados históricos
- ❌ Todas as fontes podem ser fundidas para qualquer período

### **Realidade (agora):**
- ✅ MET Norway: **Previsão apenas** (Europa, hoje + 10 dias)
- ✅ NWS: **Previsão apenas** (USA, hoje + 7 dias)
- ✅ NASA POWER: **Histórico + near-real-time** (global, 1981 - ontem)
- ✅ Open-Meteo: **Ambos** (histórico + previsão, mas bloqueado CC-BY-NC)

### **Estratégia Corrigida:**

| Período | Região | Fontes Disponíveis | Fusão? |
|---------|--------|-------------------|--------|
| **Histórico (passado)** | Global | NASA POWER | ❌ Não (fonte única) |
| **Previsão (futuro)** | Europa | NASA + MET Norway | ✅ Sim |
| **Previsão (futuro)** | USA | NASA + NWS | ✅ Sim |
| **Previsão (futuro)** | Brasil | NASA POWER | ❌ Não (fonte única) |
| **Misto (passado+futuro)** | Qualquer | Dividir em 2 períodos | ⚠️ Parcial |

---

## 🎯 Casos de Uso do EVAonline

### **Caso 1: Análise Histórica (Validação Xavier)**
```
Período: 1980-2013 (dataset Xavier)
Região: MATOPIBA (17 cidades)
Fonte: NASA POWER (única disponível)
Fusão: Não aplicável
Status: ✅ Implementado
```

### **Caso 2: ETo Recente (últimos 7 dias)**
```
Período: 2024-10-02 a 2024-10-09 (histórico)
Região: Qualquer
Fonte: NASA POWER (única disponível)
Fusão: Não aplicável
Status: ✅ Atual comportamento correto
```

### **Caso 3: Previsão de ETo (próximos 7 dias)**
```
Período: 2024-10-10 a 2024-10-17 (futuro)
Região: Paris
Fontes: NASA POWER (baseline) + MET Norway (refinamento)
Fusão: ✅ Aplicável
Status: ❌ Requer implementação
```

### **Caso 4: Período Misto (5 passado + 5 futuro)**
```
Período: 2024-10-05 a 2024-10-15
Região: Nova York
Estratégia:
  - 05-09: NASA POWER (histórico)
  - 10-15: NASA + NWS (previsão, com fusão)
  - Concatenar resultados
Status: ❌ Requer implementação complexa
```

---

## 🚀 Próximos Passos Corrigidos

### **Prioridade Alta:**
1. ✅ Manter fusão atual para casos apropriados
2. ✅ Adicionar validação de período (histórico vs previsão)
3. ✅ Warning claro quando usar dados de previsão

### **Prioridade Média:**
4. Implementar divisão de períodos mistos
5. Agregar hourly → daily para fontes de previsão

### **Prioridade Baixa:**
6. Pesos inteligentes de fusão (apenas para períodos de previsão)
7. Validação com Xavier (apenas NASA POWER histórico)

---

## 📚 Referências das APIs

### **NASA POWER**
- **Tipo:** Histórico + near-real-time
- **Período:** 1981-01-01 até ontem
- **Resolução:** Diária
- **URL:** https://power.larc.nasa.gov/api/temporal/daily/point

### **MET Norway**
- **Tipo:** Previsão (forecast)
- **Período:** Hoje + 10 dias
- **Resolução:** Horária (cada 1h ou 6h)
- **URL:** https://api.met.no/weatherapi/locationforecast/2.0/complete
- **Docs:** https://api.met.no/doc/locationforecast/datamodel

### **NWS/NOAA**
- **Tipo:** Previsão (forecast)
- **Período:** Hoje + 7 dias
- **Resolução:** Horária
- **URL:** https://api.weather.gov/gridpoints/{office}/{grid}/forecast/hourly
- **Docs:** https://www.weather.gov/documentation/services-web-api

---

**Conclusão:** O sistema atual de fusão em `data_fusion.py` está **correto** para períodos de previsão, mas precisa adicionar **validações de período** para evitar tentar fundir dados históricos com previsões (que não faria sentido). MET Norway e NWS só devem ser usados para **previsão futura**, não análise histórica.
