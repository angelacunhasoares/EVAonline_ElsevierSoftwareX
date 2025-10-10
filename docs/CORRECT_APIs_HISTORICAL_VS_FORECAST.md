# 🔄 APIs Corretas: Dados Históricos vs Previsão

## 📊 Análise Corrigida das APIs

Você estava **absolutamente correto**! Ambas as fontes têm APIs separadas para **dados históricos** e **previsão**:

---

## 🇳🇴 MET Norway - Duas APIs Diferentes

### **1. LocationForecast API** (Previsão - Já implementado ✅)
- **URL:** `https://api.met.no/weatherapi/locationforecast/2.0`
- **Tipo:** Previsão meteorológica
- **Resolução:** Horária
- **Período:** Próximos 7-10 dias
- **Uso atual:** `met_norway_client.py` já usa esta API

### **2. Frost API** (Dados Históricos - **NÃO implementado** ❌)
- **URL:** `https://frost.met.no/observations/v0.jsonld`
- **Tipo:** Observações históricas
- **Resolução:** Diária, mensal, anual
- **Período:** Arquivo completo de dados históricos
- **Licença:** CC-BY 4.0 (mesma)
- **Requisitos:** Autenticação via client ID (gratuito)
- **Documentação:** https://frost.met.no/

**Variáveis disponíveis (Frost):**
```
- air_temperature (daily max/min/mean)
- relative_humidity
- wind_speed
- precipitation_amount
- surface_downwelling_shortwave_flux_in_air (radiação solar)
```

---

## 🇺🇸 NOAA/NWS - Duas APIs Diferentes

### **1. Weather.gov API** (Previsão - Já implementado ✅)
- **URL:** `https://api.weather.gov/gridpoints/.../forecast/hourly`
- **Tipo:** Previsão meteorológica
- **Resolução:** Horária
- **Período:** Próximos 7 dias
- **Uso atual:** `nws_client.py` já usa esta API

### **2. NCEI Climate Data Online (CDO) API** (Dados Históricos - **NÃO implementado** ❌)
- **URL:** `https://www.ncei.noaa.gov/cdo-web/api/v2/data`
- **Tipo:** Observações históricas
- **Resolução:** Diária, mensal, anual
- **Período:** Arquivo completo (1763 - presente para alguns locais)
- **Licença:** Domínio Público
- **Requisitos:** Token de acesso (gratuito)
- **Documentação:** https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation

**Datasets disponíveis (NCEI):**
```
- GHCN-Daily (Global Historical Climatology Network - Daily)
  * TMAX, TMIN, TAVG (temperatura)
  * PRCP (precipitação)
  * SNOW (neve)
  * AWND (velocidade do vento)
```

---

## 🎯 Implicações para o EVAonline

### **Situação Atual:**
```
✅ NASA POWER (histórico global) - Implementado
✅ MET Norway LocationForecast (previsão Europa) - Implementado  
✅ NWS Weather.gov (previsão USA) - Implementado
❌ MET Norway Frost (histórico Europa) - NÃO implementado
❌ NOAA NCEI (histórico USA) - NÃO implementado
❌ Open-Meteo Archive (histórico global) - Bloqueado por licença
```

### **Problema Identificado:**

Para cálculo de ETo **histórico** (período passado), temos:
- ✅ **Global:** NASA POWER (único disponível)
- ❌ **Europa:** Sem dados históricos (apenas previsão MET)
- ❌ **USA:** Sem dados históricos (apenas previsão NWS)

Para cálculo de ETo **previsão** (próximos dias), temos:
- ✅ **Global:** NASA POWER (até amanhã)
- ✅ **Europa:** MET Norway LocationForecast (7-10 dias)
- ✅ **USA:** NWS Weather.gov (7 dias)

---

## 📋 Estratégias de Fusão Corrigidas

### **Cenário 1: Dados Históricos (período passado)**

**Paris, França - Janeiro 2024:**
```
Fontes disponíveis:
✅ NASA POWER (histórico global diário)
❌ MET Norway LocationForecast (só previsão)
❌ MET Norway Frost (histórico, mas requer implementação)

Solução atual: Usar apenas NASA POWER
Solução futura: Implementar Frost API para fusão NASA + Frost
```

**Nova York, USA - Janeiro 2024:**
```
Fontes disponíveis:
✅ NASA POWER (histórico global diário)
❌ NWS Weather.gov (só previsão)
❌ NOAA NCEI (histórico, mas requer implementação)

Solução atual: Usar apenas NASA POWER
Solução futura: Implementar NCEI API para fusão NASA + NCEI
```

### **Cenário 2: Previsão (próximos 7 dias)**

**Paris, França - Próximos 7 dias:**
```
Fontes disponíveis:
✅ NASA POWER (até +1 dia, limitado)
✅ MET Norway LocationForecast (7-10 dias, horário)

Solução: Fusão NASA POWER + MET LocationForecast
- NASA: Baseline global
- MET: Refinamento regional para Europa
```

**Nova York, USA - Próximos 7 dias:**
```
Fontes disponíveis:
✅ NASA POWER (até +1 dia, limitado)
✅ NWS Weather.gov (7 dias, horário)

Solução: Fusão NASA POWER + NWS Weather.gov
- NASA: Baseline global
- NWS: Refinamento regional para USA
```

---

## 🚀 Plano de Ação Atualizado

### **Fase 1: Manter Implementação Atual** ✅
```
Status: COMPLETO
- NASA POWER client (global, histórico + previsão limitada)
- MET Norway client (Europa, previsão)
- NWS client (USA, previsão)
```

### **Fase 2: Validar Uso Correto das APIs** ⚠️
```
CRÍTICO: Ajustar data_download.py para distinguir:

1. Período PASSADO (< hoje):
   - Usar apenas NASA POWER (único histórico disponível)
   - MET e NWS não aplicáveis (só previsão)

2. Período FUTURO (>= hoje, próximos 7 dias):
   - Europa: Fusão NASA + MET LocationForecast
   - USA: Fusão NASA + NWS Weather.gov
   - Outros: Apenas NASA POWER
```

### **Fase 3: Implementar APIs Históricas** (Futuro)
```
Prioridade BAIXA (opcional para melhorar fusão):

1. MET Norway Frost API
   - Endpoint: https://frost.met.no/observations/v0.jsonld
   - Requer: Client ID (gratuito)
   - Benefício: Dados históricos Europa para fusão

2. NOAA NCEI CDO API
   - Endpoint: https://www.ncei.noaa.gov/cdo-web/api/v2/data
   - Requer: Access token (gratuito)
   - Benefício: Dados históricos USA para fusão

3. Atualizar data_download.py:
   - Detectar período (histórico vs previsão)
   - Escolher APIs apropriadas automaticamente
```

---

## 🔄 Lógica de Seleção de Fontes (Corrigida)

```python
def select_sources_for_period(
    lat: float,
    lon: float,
    start_date: datetime,
    end_date: datetime,
    requested_sources: List[str]
) -> Dict[str, List[str]]:
    """
    Seleciona fontes apropriadas baseado no período.
    
    Returns:
        {
            'available': ['source1', 'source2'],
            'reason': 'Historical data requested, using NASA POWER only'
        }
    """
    today = datetime.now().date()
    is_historical = end_date.date() < today
    is_forecast = start_date.date() >= today
    is_mixed = start_date.date() < today <= end_date.date()
    
    # Detectar cobertura geográfica
    manager = ClimateSourceManager()
    geographic_coverage = manager.get_available_sources_for_location(
        lat, lon, exclude_non_commercial=True
    )
    
    available = []
    reason = ""
    
    if is_historical:
        # PERÍODO PASSADO: Apenas fontes com dados históricos
        if 'nasa_power' in requested_sources:
            available.append('nasa_power')
        
        # MET Frost e NOAA NCEI quando implementados
        if 'met_norway_frost' in requested_sources:  # Future
            if geographic_coverage.get('met_norway_frost', {}).get('available'):
                available.append('met_norway_frost')
        
        if 'noaa_ncei' in requested_sources:  # Future
            if geographic_coverage.get('noaa_ncei', {}).get('available'):
                available.append('noaa_ncei')
        
        reason = (
            "Historical period requested. Using archives: " + 
            ", ".join(available)
        )
    
    elif is_forecast:
        # PERÍODO FUTURO: Fontes com previsão
        for source in requested_sources:
            if source in ['met_norway', 'nws_usa']:
                # Validar cobertura
                if geographic_coverage.get(source, {}).get('available'):
                    available.append(source)
            elif source == 'nasa_power':
                available.append(source)  # Sempre disponível
        
        reason = (
            "Forecast period requested. Using: " + 
            ", ".join(available)
        )
    
    else:  # is_mixed
        # PERÍODO MISTO: Priorizar histórico
        available = ['nasa_power']  # Baseline
        reason = (
            "Mixed period (past + future). Using NASA POWER for "
            "consistency. Consider splitting requests."
        )
    
    return {
        'available': available,
        'reason': reason,
        'warnings': [] if available else [
            "No sources available for this period and location"
        ]
    }
```

---

## 📊 Tabela de Capacidades (Atualizada)

| Fonte | Tipo | Resolução | Cobertura | Período | Status |
|-------|------|-----------|-----------|---------|--------|
| **NASA POWER** | Histórico + Previsão limitada | Diária | Global | 1981-presente + 1 dia futuro | ✅ Implementado |
| **MET LocationForecast** | Previsão | Horária | Europa | Próximos 7-10 dias | ✅ Implementado |
| **MET Frost** | Histórico | Diária/Mensal | Europa | Arquivo completo | ❌ Não implementado |
| **NWS Weather.gov** | Previsão | Horária | USA | Próximos 7 dias | ✅ Implementado |
| **NOAA NCEI** | Histórico | Diária | USA | 1763-presente | ❌ Não implementado |
| **Open-Meteo Archive** | Histórico | Horária | Global | 1940-presente | ⛔ Bloqueado (CC-BY-NC) |

---

## ✅ Ações Imediatas

### **1. Corrigir `data_download.py`** 🔴 CRÍTICO

**Problema atual:** Tenta usar MET/NWS para dados históricos (não funciona)

**Solução:**
```python
# Adicionar detecção de período
today = datetime.now().date()

if data_final_formatted.date() < today:
    # HISTÓRICO: Apenas NASA POWER disponível
    logger.info("Historical period requested, using NASA POWER only")
    
    if 'met_norway' in sources or 'nws_usa' in sources:
        warnings_list.append(
            "⚠️ MET Norway and NWS provide forecast only. "
            "Using NASA POWER for historical data."
        )
        sources = ['nasa_power']  # Forçar apenas NASA

elif data_inicial_formatted.date() >= today:
    # PREVISÃO: NASA + MET/NWS conforme cobertura
    logger.info("Forecast period requested")
    # Validar cobertura geográfica (código existente)

else:
    # MISTO: Avisar usuário
    warnings_list.append(
        "⚠️ Period spans past and future. For best results, "
        "split into two separate requests."
    )
```

### **2. Atualizar Documentação** 🟡 IMPORTANTE

**Atualizar:**
- `SOURCES_CONFIG` em `climate_source_manager.py`
- Adicionar campo `"data_type": "forecast" | "historical" | "both"`
- Documentar limitações de cada fonte

### **3. Validar Casos de Teste** 🟢 RECOMENDADO

**Testar:**
```python
# Caso 1: Histórico (deve usar só NASA)
download_weather_data(
    data_source=['nasa_power', 'met_norway'],
    data_inicial='2024-01-01',  # Passado
    data_final='2024-01-07',
    latitude=48.8566,
    longitude=2.3522
)
# Esperado: Apenas NASA POWER, warning sobre MET

# Caso 2: Previsão (deve usar ambos)
download_weather_data(
    data_source=['nasa_power', 'met_norway'],
    data_inicial=datetime.now().strftime('%Y-%m-%d'),  # Hoje
    data_final=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
    latitude=48.8566,
    longitude=2.3522
)
# Esperado: NASA + MET em fusão
```

---

## 🎯 Conclusão

**Você estava correto desde o início!** MET Norway e NWS **têm** dados históricos, mas através de **APIs diferentes**:

- ✅ **Implementado:** APIs de previsão (LocationForecast, Weather.gov)
- ❌ **Não implementado:** APIs históricas (Frost, NCEI)

**Estratégia recomendada:**

1. **Curto prazo:** Corrigir `data_download.py` para usar apenas NASA POWER em períodos históricos
2. **Médio prazo:** Implementar Frost API e NCEI API para fusão completa
3. **Longo prazo:** Criar seleção automática de APIs baseada em período + cobertura

**Benefício da correção:**
- ✅ Evita erros ao tentar dados históricos de APIs de previsão
- ✅ Mantém fusão funcional para previsões (Europa/USA)
- ✅ Prepara terreno para implementação de APIs históricas futuras

---

**Próximo passo:** Implementar a detecção de período em `data_download.py`?
