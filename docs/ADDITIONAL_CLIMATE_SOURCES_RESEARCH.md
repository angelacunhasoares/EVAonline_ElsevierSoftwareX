# Pesquisa Adicional de Fontes de Dados Climáticos
## EVAonline - Análise de Novas Fontes para Fusão de Dados

**Data da Pesquisa:** 08/10/2025  
**Objetivo:** Identificar fontes de dados climáticos adicionais com licenças adequadas para uso comercial e fusão de dados

---

## 🎯 Critérios de Seleção

### ✅ Requisitos Obrigatórios
1. **Licença:** Domínio Público ou Creative Commons compatível com uso comercial
2. **API REST:** Interface simples (JSON/XML), sem GRIB2
3. **Cobertura:** Global ou regional relevante (Brasil, América, Europa)
4. **Variáveis:** Temperatura, umidade, vento, radiação solar, precipitação
5. **Temporal:** Dados diários ou horários com delay < 7 dias
6. **Estabilidade:** Uptime > 99%, documentação completa

### ❌ Critérios de Exclusão
- Licenças não-comerciais (CC-BY-NC)
- APIs pagas sem tier gratuito razoável
- Formatos complexos (GRIB2, HDF5, NetCDF sem API REST)
- Delay > 7 dias (exceto validação histórica)
- Cobertura limitada a países não relevantes

---

## 🌟 NOVAS FONTES RECOMENDADAS

### 1. OpenWeatherMap (❌ PAGO - ASSINATURA OBRIGATÓRIA)

**Website:** https://openweathermap.org/  
**Status:** ❌ **NÃO APROVADO - REQUER ASSINATURA PAGA**

### ⚠️ DESCOBERTA CRÍTICA: One Call API 3.0 Requer Assinatura Separada

**Segundo a página oficial de pricing (https://openweathermap.org/price):**

> "One Call API 3.0 is included in the **'One Call by Call' subscription ONLY**. This separate subscription includes 1,000 calls/day for free..."

**IMPORTANTE:** One Call API 3.0 NÃO está incluída no free tier básico do OpenWeatherMap! O tier gratuito padrão (60 calls/min, 1M calls/mês) fornece apenas:
- Current Weather API
- 3-hour Forecast for 5 days
- Basic Weather Maps (5 layers)
- Air Pollution API
- Geocoding API

Para acessar **One Call API 3.0** (current + minutely + hourly + daily + historical), é necessária **assinatura separada**.

#### Licenciamento
- **Tier Gratuito BÁSICO:** ❌ NÃO inclui One Call 3.0
- **One Call 3.0 Subscription:** 1k calls/dia grátis + £0.0012 GBP/call adicional
- **Licença:** CC-BY-SA 4.0 + ODbL (com **ShareAlike requirement** ⚠️)
- **ShareAlike Problem:** Produtos derivados DEVEM usar mesma licença open
- **Uso Comercial:** Requer licença "OpenWeather for Business" (£30-£1200/mês)

#### Cobertura & Dados (One Call API 3.0 - PAGA)
- **Cobertura:** Global (200.000+ estações meteorológicas)
- **Resolução Temporal:** 
  - Current: tempo real
  - Minutely: 1 hora (1-min intervals)
  - Hourly: 48 horas
  - Daily: 8 dias
- **Histórico:** Desde 1979 (46+ anos) - APENAS com assinatura
- **Variáveis:** Temperatura, umidade, vento, precipitação, UV index, pressão

#### API Gratuita Básica (SEM One Call 3.0)
- **Current Weather API:** Dados atuais apenas
- **5-day/3-hour Forecast:** Previsão básica apenas
- **Sem minutely, sem hourly 48h, sem daily 8d, sem historical**

#### Solar Irradiance API (Separada)
**Preço:** £0.1 GBP por API call (!!!!)
- GHI (Global Horizontal Irradiance)
- DNI (Direct Normal Irradiance)  
- DHI (Diffuse Horizontal Irradiance)
- **NÃO gratuita!**

#### Vantagens (se pagar assinatura)
✅ API extremamente bem documentada  
✅ One Call 3.0: current + minutely + hourly + daily + historical  
✅ Solar irradiance API dedicada (mas PAGA: £0.1/call!)  
✅ Daily aggregation disponível  
✅ JSON format simples  
✅ 99.9% uptime garantido  
✅ Global coverage excelente  

#### Limitações CRÍTICAS
❌ **One Call API 3.0 requer assinatura separada (não é free tier!)**  
❌ **CC-BY-SA 4.0 com ShareAlike requirement** (produtos derivados devem ser open)  
❌ **Solar Irradiance API custa £0.1 por call** (não gratuita!)  
❌ Uso comercial real requer "OpenWeather for Business" (£30-£1200/mês)  
❌ Free tier básico muito limitado (sem one-call features)  
❌ Historical bulk data requer assinatura Professional+ (£370/mês)  
⚠️ ShareAlike incompatível com software proprietário/comercial fechado  

#### Recomendação FINAL
**USO:** ❌ **NÃO RECOMENDADO para EVAonline**  
**MOTIVO 1:** One Call 3.0 não está no free tier (requer subscription)  
**MOTIVO 2:** CC-BY-SA 4.0 ShareAlike problemático para uso comercial  
**MOTIVO 3:** Solar API paga (£0.1/call = £100 para 1k calls!)  
**ALTERNATIVA:** Usar NASA POWER (gratuito, domínio público, tem solar radiation)  
**IMPLEMENTAÇÃO:** ❌ **NÃO IMPLEMENTAR** (custos ocultos + licensing issues)

---

### 2. Visual Crossing Weather API (⭐⭐⭐⭐⭐ ALTAMENTE RECOMENDADO)

**Website:** https://www.visualcrossing.com/weather-api  
**Status:** ✅ **APROVADO PARA FUSÃO**

#### Licenciamento
- **Tier Gratuito:** 1.000 registros/dia (Timeline Weather API)
- **Licença:** Comercial permitido explicitamente
- **Atribuição:** Não obrigatória

#### Cobertura & Dados
- **Cobertura:** Global (100.000+ estações + modelos alta resolução)
- **Resolução Temporal:**
  - Sub-horária (15 minutos)
  - Horária
  - Diária
- **Histórico:** 50+ anos de dados históricos
- **Forecast:** 15 dias model-based + statistical forecast
- **Variáveis:** 
  - Core: Temp, RH, vento, precipitação
  - Agricultura: **Evapotranspiração**, soil temperature, soil moisture
  - Solar: GHI, DNI, sun elevation, diffuse radiation
  - Vento: 10m, 50m, 80m, 100m height
  - Maritimo: Wave height, swell

#### Vantagens EXCEPCIONAIS
✅ **EVAPOTRANSPIRAÇÃO DIRETA** (não precisa calcular!)  
✅ **SOIL MOISTURE** (umidade do solo)  
✅ **SOLAR RADIATION** completa (GHI, DNI, diffuse)  
✅ Single API endpoint para current + forecast + history  
✅ CSV e JSON output  
✅ Sub-hourly data (15 min intervals)  
✅ 50+ anos histórico (1970+)  
✅ Address geocoding built-in  
✅ Statistical forecast além de 15 dias  
✅ Historical forecast (previsões passadas)  
✅ Sem necessidade de atribuição  

#### Limitações
⚠️ 1.000 records/dia no free tier  
⚠️ "Records" conta cada dia x location (1 cidade x 10 dias = 10 records)  
⚠️ Para 337 cidades MATOPIBA precisa gerenciar requests cuidadosamente  

#### Recomendação
**USO:** **Fonte PREMIUM para agricultura e ETo**  
**PRIORIDADE:** 1 (mesma que OpenWeatherMap)  
**IMPLEMENTAÇÃO:** **PRIORITÁRIO** - tem evapotranspiração pronta!

---

### 3. WeatherAPI.com (⭐⭐ LIMITADO NO FREE TIER)

**Website:** https://www.weatherapi.com/  
**Status:** ⚠️ **LIMITADO - FREE TIER COM RESTRIÇÕES**

#### Licenciamento
- **Tier Gratuito:** 1 milhão calls/**MÊS** (não diário!)
- **Licença:** Comercial e não-comercial permitidos
- **Atribuição:** Link back obrigatório no free tier

#### ⚠️ RESTRIÇÕES CRÍTICAS DO FREE TIER:

Segundo a tabela de pricing (https://www.weatherapi.com/pricing.aspx):

| Recurso | Free Tier | Plano Pago |
|---------|-----------|------------|
| **Forecast** | 3 dias apenas | 7-14 dias |
| **Forecast Interval** | Daily e Hourly | Daily, Hourly, 15-min |
| **Marine Weather** | 1 dia, SEM tide data | 3-7 dias, COM tide |
| **Historical** | Últimos 7 dias apenas | 2010-presente |
| **Future Weather** | ❌ NÃO | 300-365 dias |
| **Air Quality** | ⚠️ Limitado | Completo |
| **Evapotranspiration** | ❌ NÃO (só pago) | ✅ SIM |
| **Soil Data** | ❌ NÃO | ✅ SIM |
| **Solar Irradiance** | ⚠️ Limitado | Completo |
| **Pollen** | ❌ NÃO | ✅ SIM |
| **15-min intervals** | ❌ NÃO | ✅ SIM |
| **Uptime SLA** | 95.5% | 99-100% |

#### Vantagens (limitadas no free)
✅ 1 milhão calls/mês (~33k/dia)  
✅ Forecast 3 dias (daily + hourly)  
✅ Histórico últimos 7 dias  
✅ Real-time current weather  
✅ Basic variables (temp, humidity, wind, precip)  

#### Limitações CRÍTICAS
❌ **SEM EVAPOTRANSPIRAÇÃO no free tier!**  
❌ **SEM SOIL DATA no free tier!**  
❌ Histórico apenas 7 dias (vs 2010+ no pago)  
❌ Forecast apenas 3 dias (vs 14 no pago)  
❌ Marine weather limitado (sem tide data)  
❌ Air quality limitado  
❌ Solar irradiance limitado  
❌ 95.5% uptime (vs 99%+ pago)  

#### Recomendação ATUALIZADA
**USO:** ⚠️ **NÃO RECOMENDADO para EVAonline**  
**MOTIVO:** Falta evapotranspiração e soil data no free tier  
**ALTERNATIVA:** Visual Crossing (tem ET no free) ou OpenWeatherMap  
**IMPLEMENTAÇÃO:** ❌ **NÃO IMPLEMENTAR** (limitações críticas)

---

### 4. ERA5 Reanalysis (⭐⭐⭐ VALIDAÇÃO APENAS)

**Website:** https://cds.climate.copernicus.eu/  
**Status:** ⚠️ **VALIDAÇÃO HISTÓRICA APENAS** (não tempo real)

#### Licenciamento
- **Tier Gratuito:** Ilimitado (requer registro)
- **Licença:** CC-BY 4.0 (comercial permitido com atribuição)
- **Atribuição:** Obrigatória (ECMWF Copernicus)

#### Cobertura & Dados
- **Cobertura:** Global
- **Resolução Espacial:** 0.25° x 0.25° (~31 km)
- **Resolução Temporal:** Horária
- **Histórico:** 1940-presente (reanalysis)
- **Delay:** ~5 dias (dados recentes)
- **Variáveis:** Todos os parâmetros atmosféricos (100+ variáveis)

#### Vantagens
✅ Cobertura global completa desde 1940  
✅ Resolução horária  
✅ Qualidade científica altíssima (reanalysis)  
✅ Todas variáveis meteorológicas  
✅ Usado como referência científica mundial  
✅ API Python (cdsapi) bem documentada  
✅ Gratuito e ilimitado  

#### Limitações
⚠️ Delay ~5 dias (reanalysis, não real-time)  
⚠️ Download pode ser lento para grandes volumes  
⚠️ Requer registro no Copernicus CDS  
⚠️ NetCDF format (requer processamento)  
⚠️ Complexidade maior que REST APIs simples  

#### Recomendação
**USO:** Validação científica histórica  
**PRIORIDADE:** N/A (não para tempo real)  
**IMPLEMENTAÇÃO:** Alternativa/complemento ao AgERA5 para validação

---

## 📊 COMPARAÇÃO GERAL

### Fontes para Fusão de Dados (Tempo Real)

| Fonte | Licença | Free Tier | ETo Direto | Cobertura | Prioridade | Implementar? |
|-------|---------|-----------|------------|-----------|------------|--------------|
| **Visual Crossing** | Comercial ✅ | 1k rec/dia | **SIM** ✅ | Global | **1** | **✅ SIM (PRIORITÁRIO)** |
| **OpenWeatherMap** | Comercial ✅ | 1k calls/dia | Não | Global | **2** | **✅ SIM** |
| NASA POWER | Domínio Público ✅ | 1k calls/dia | Não | Global | 2 | ✅ JÁ IMPLEMENTADO |
| MET Norway | CC-BY 4.0 ✅ | Ilimitado | Não | Europa | 3 | ✅ JÁ IMPLEMENTADO |
| NWS (NOAA) | Domínio Público ✅ | Ilimitado | Não | USA | 4 | ✅ JÁ IMPLEMENTADO |
| ~~WeatherAPI.com~~ | Comercial ⚠️ | 1M calls/mês | **NÃO no free** ❌ | Global | N/A | ❌ **NÃO (sem ET no free)** |
| Open-Meteo | CC-BY-NC ❌ | 10k calls/dia | Não | Global | N/A | ❌ **APENAS VISUALIZAÇÃO** |

### Fontes para Validação Histórica

| Fonte | Licença | Período | Resolução | Delay | Implementar? |
|-------|---------|---------|-----------|-------|--------------|
| Xavier BR | Acadêmico | 1961-2024 | 0.25° | N/A | ✅ JÁ DOCUMENTADO |
| AgERA5 | CC-BY 4.0 ✅ | 1979-presente | 0.1° | ~7 dias | ✅ JÁ DOCUMENTADO |
| ERA5 | CC-BY 4.0 ✅ | 1940-presente | 0.25° | ~5 dias | ⚠️ OPCIONAL |

---

## 🎯 RECOMENDAÇÕES FINAIS

### 1. Implementação Prioritária: Visual Crossing Weather API

**Motivo:** É a **ÚNICA fonte gratuita** que fornece **evapotranspiração diretamente** + soil moisture + dados agrícolas completos no free tier.

**Impacto no EVAonline:**
- ✅ Não precisa calcular ETo (já vem calculada)
- ✅ Pode comparar ETo calculada vs ETo API (validação)
- ✅ Soil moisture para análises avançadas
- ✅ 50+ anos histórico
- ✅ Licença comercial limpa
- ✅ **1.000 records/dia suficiente para MATOPIBA** (337 cidades × 2 dias = 674 records)

**Implementação:**
```python
# Exemplo de chamada Visual Crossing
url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{lat},{lon}/{start_date}/{end_date}"
params = {
    "key": API_KEY,
    "include": "days",
    "elements": "datetime,temp,humidity,windspeed,solarradiation,et,soilmoisture",
    "unitGroup": "metric"
}
# Response inclui: "et" (evapotranspiration mm/day) direto!
```

---

### 2. Implementação Secundária: OpenWeatherMap

**Motivo:** API mais popular do mundo (750M+ requests/dia), extremamente confiável, boa documentação. Sem restrições críticas no free tier.

**Vantagens:**
- ✅ Solar irradiance API separada (GHI, DNI, DHI)
- ✅ 46 anos histórico
- ✅ One Call API 3.0 (tudo em 1 chamada)
- ✅ Comercial permitido
- ✅ Todas variáveis básicas sem restrição
- ✅ 1.000 calls/dia suficiente para MATOPIBA

**Uso no EVAonline:**
- Fonte primária global para radiação solar detalhada
- Backup para Visual Crossing
- Historical weather queries
- Fonte complementar para fusão de dados

---

### 3. ❌ NÃO Implementar: WeatherAPI.com

**Motivo:** **Evapotranspiração NÃO disponível no free tier**, que é o recurso mais importante para o EVAonline.

**Limitações Críticas no Free:**
- ❌ Sem evapotranspiração
- ❌ Sem soil data
- ❌ Histórico apenas 7 dias (vs 2010+ no pago)
- ❌ Forecast apenas 3 dias
- ❌ Air quality limitado
- ❌ 95.5% uptime (baixo para produção)

**Conclusão:** Apesar do volume alto (1M calls/mês), as restrições de variáveis críticas inviabilizam uso para cálculo de ETo.

---

## 📋 CONFIGURAÇÃO RECOMENDADA FINAL

### SOURCES_CONFIG Atualizado

```python
SOURCES_CONFIG = {
    # Tier 1 - Globais com ETo direto (PRIORITÁRIO)
    "visual_crossing": {
        "id": "visual_crossing",
        "name": "Visual Crossing Weather",
        "coverage": "global",
        "temporal": "daily",  # também hourly e 15-min disponíveis
        "bbox": None,
        "license": "commercial_ok",
        "realtime": True,
        "priority": 1,  # MAIOR PRIORIDADE
        "url": "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline",
        "variables": [
            "temp", "tempmax", "tempmin", "humidity", "windspeed",
            "solarradiation",  # W/m²
            "et0",  # ⭐ EVAPOTRANSPIRAÇÃO DIRETA (mm/dia)
            "soilmoisture", "soiltemp", "precip", "dewpoint",
            "solarenergy",  # MJ/m²
            "uvindex"
        ],
        "delay_hours": 1,
        "update_frequency": "hourly",
        "historical_start": "1970-01-01",
        "forecast_days": 15,
        "restrictions": {
            "limit_requests": 1000,  # 1000 records/dia
            "attribution_required": False
        },
        "use_case": "Primary global ETo source with direct ET data + soil moisture"
    },
    
    "openweathermap": {
        "id": "openweathermap",
        "name": "OpenWeatherMap",
        "coverage": "global",
        "temporal": "hourly",  # também daily
        "bbox": None,
        "license": "commercial_ok",
        "realtime": True,
        "priority": 2,
        "url": "https://api.openweathermap.org/data/3.0/onecall",
        "solar_url": "https://api.openweathermap.org/data/3.0/solar",
        "variables": [
            "temp", "humidity", "wind_speed", "clouds",
            "uvi", "pressure", "dew_point", "rain",
            "temp_min", "temp_max"  # daily data
        ],
        "solar_variables": [
            "ghi",  # Global Horizontal Irradiance (W/m²)
            "dni",  # Direct Normal Irradiance (W/m²)
            "dhi"   # Diffuse Horizontal Irradiance (W/m²)
        ],
        "delay_hours": 1,
        "update_frequency": "hourly",
        "historical_start": "1979-01-01",
        "forecast_days": 8,
        "restrictions": {
            "limit_requests": 1000,  # 1k calls/dia free tier
            "attribution_required": True
        },
        "use_case": "Global daily ETo calculation, solar irradiance detailed, historical data"
    },
    
    # NASA POWER continua como está (já implementado)
    "nasa_power": {
        "id": "nasa_power",
        "name": "NASA POWER",
        "coverage": "global",
        "temporal": "daily",
        "bbox": None,
        "license": "public_domain",
        "realtime": False,
        "priority": 3,
        "url": "https://power.larc.nasa.gov/api/temporal/daily/point",
        "variables": [
            "T2M_MAX", "T2M_MIN", "T2M", "RH2M", "WS2M",
            "ALLSKY_SFC_SW_DWN",  # Solar radiation
            "PRECTOTCORR"
        ],
        "delay_hours": 72,  # 2-3 dias
        "update_frequency": "daily",
        "historical_start": "1981-01-01",
        "restrictions": {
            "limit_requests": 1000
        },
        "use_case": "Global daily ETo backup, long historical data"
    },
    
    # MET Norway continua como está (já implementado)
    "met_norway": { ... },
    
    # NWS continua como está (já implementado)
    "nws_usa": { ... }
}
```

### Fontes REMOVIDAS/NÃO IMPLEMENTADAS:

```python
# ❌ REMOVIDO - Licença CC-BY-NC problemática
# "openmeteo": { ... }

# ❌ NÃO IMPLEMENTAR - Sem ET no free tier
# "weatherapi_com": { ... }

# ❌ REMOVIDO - GRIB2 complexo
# "gfs_noaa": { ... }
```

---

## 🚀 PLANO DE IMPLEMENTAÇÃO REVISADO

### ⚠️ DESCOBERTA CRÍTICA: Todas as Novas Fontes Rejeitadas

Após análise detalhada dos termos de serviço e pricing, **TODAS as 3 fontes pesquisadas foram rejeitadas**:

| Fonte | Motivo de Rejeição | Status |
|-------|-------------------|---------|
| **OpenWeatherMap** | ❌ One Call 3.0 requer assinatura paga separada | REJEITADO |
| | ❌ CC-BY-SA ShareAlike problemático para comercial | |
| | ❌ Solar API custa £0.1/call (não gratuita) | |
| **Visual Crossing** | ❌ Evapotranspiração APENAS em Corporate $150/mês | REJEITADO |
| | ❌ Professional $35/mês NÃO inclui ET/soil | |
| | ❌ Free tier não tem dados agrícolas | |
| **WeatherAPI.com** | ❌ Free tier NÃO inclui evapotranspiração | REJEITADO |
| | ❌ Free tier NÃO inclui soil data | |
| | ❌ Histórico apenas 7 dias (vs 2010+ pago) | |

### ✅ FONTES VALIDADAS E APROVADAS (já implementadas)

**USAR APENAS:**
1. **NASA POWER** (domínio público, global, todas variáveis FAO-56)
2. **MET Norway** (CC-BY 4.0, Europa, dados meteorológicos completos)
3. **NWS/NOAA** (domínio público, USA, dados oficiais governo)

### 📊 ANÁLISE DE CUSTOS REVISADA

**Cenário MATOPIBA Heatmap (337 cidades, diário):**

| Fonte | Custo Real Free Tier | Tem ET? | Status |
|-------|---------------------|---------|--------|
| NASA POWER | ✅ GRATUITO | ❌ Calcula (FAO-56) | ✅ USAR |
| MET Norway | ✅ GRATUITO | ❌ Calcula (FAO-56) | ✅ USAR |
| NWS USA | ✅ GRATUITO | ❌ Calcula (FAO-56) | ✅ USAR |
| OpenWeatherMap | ❌ Requer assinatura One Call 3.0 | ❌ Calcula | ❌ NÃO USAR |
| Visual Crossing | ❌ $150/mês p/ ET (Corporate) | ❌ NO free tier | ❌ NÃO USAR |
| WeatherAPI.com | ❌ Sem ET no free | ❌ Só em pago | ❌ NÃO USAR |

### ~~Fase 1: Visual Crossing~~ ❌ CANCELADA
**Motivo:** Evapotranspiração requer Corporate plan ($150/mês) - proibitivo para projeto acadêmico

### ~~Fase 2: OpenWeatherMap~~ ❌ CANCELADA  
**Motivo:** One Call 3.0 requer assinatura separada + ShareAlike licensing issues + Solar API paga

### ~~Fase 3: WeatherAPI.com~~ ❌ CANCELADA
**Motivo:** Free tier não inclui evapotranspiração nem soil data (variáveis críticas para EVAonline)

---

## 💰 ANÁLISE DE CUSTOS (FREE TIERS) - REALIDADE

### Cenário MATOPIBA Heatmap (337 cidades, diário)

| Fonte | Limite Free | Uso Diário | Suficiente? | Tem ET? | **CUSTO REAL** |
|-------|-------------|------------|-------------|---------|----------------|
| NASA POWER | 1k calls/dia | 337 cidades | ✅ SIM | ❌ Calcula | **$0/mês** ✅ |
| MET Norway | Ilimitado | 337 cidades | ✅ SIM | ❌ Calcula | **$0/mês** ✅ |
| NWS USA | Ilimitado | Não aplicável | N/A | ❌ Calcula | **$0/mês** ✅ |
| OpenWeatherMap | ❌ Requer subscription | N/A | ❌ NÃO | ❌ Calcula | **£0.0012/call** após 1k |
| Visual Crossing | 1k rec/dia FREE | 337 cidades | ⚠️ SIM | ❌ **NO free** | **$150/mês** p/ ET |
| WeatherAPI.com | 1M calls/**mês** | ~33k/dia | ✅ SIM | ❌ **NO free** | **$X/mês** p/ ET |

### ⚠️ CONCLUSÃO: Nenhuma Fonte Nova Viável

**Realidade descoberta:**
1. ❌ **OpenWeatherMap:** One Call 3.0 não está no free tier básico, requer subscription separada
2. ❌ **Visual Crossing:** Evapotranspiração requer Corporate plan ($150/mês mínimo)
3. ❌ **WeatherAPI.com:** Evapotranspiração e soil data excluídos do free tier

**Implicação para EVAonline:**
- ✅ **Continuar usando** NASA POWER, MET Norway, NWS (100% gratuitos)
- ✅ **Calcular ETo** usando Penman-Monteith FAO-56 (já implementado)
- ❌ **NÃO adicionar** novas fontes comerciais (custos proibitivos)
- 📚 **Foco:** Melhorar algoritmo de fusão com fontes existentes

---

## 📚 LIÇÕES APRENDIDAS: Como Avaliar APIs Climáticas

### ⚠️ Armadilhas Comuns em Marketing de APIs

**1. "Free Tier" NÃO significa "Todas as Features Gratuitas"**
- ❌ OpenWeatherMap: "Free tier" não inclui One Call API 3.0
- ❌ Visual Crossing: "Free tier" não inclui evapotranspiração
- ❌ WeatherAPI.com: "Free tier" não inclui ET, soil, dados avançados

**2. Marketing vs Realidade de Pricing**
- 📄 **Página de Features:** Lista TODAS as capabilities (pagas e gratuitas misturadas)
- 💰 **Página de Pricing:** Revela O QUE está em cada tier (verdade escondida)
- ⚠️ **Sempre checar pricing page ANTES de planejar implementação!**

**3. Confusão Intencional: Mensal vs Diário**
- ❌ "1M calls/mês" ≠ "1M calls/dia" 
- ✅ 1M calls/mês = ~33k calls/dia (realidade)
- 📊 WeatherAPI.com marketing inicial ambíguo sobre período

**4. Variáveis Agrícolas = Premium Tier**
- ❌ Evapotranspiração, soil moisture, pollen → SEMPRE em planos pagos
- ❌ Free tiers focam em: temp, humidity, wind, precip (básico)
- ✅ NASA POWER única exceção: domínio público, TODAS variáveis gratuitas

**5. Licensing "ShareAlike" Pode Ser Problemático**
- ⚠️ CC-BY-SA 4.0 (OpenWeatherMap) exige produtos derivados usem mesma licença
- ⚠️ Incompatível com software proprietário fechado
- ⚠️ Pode bloquear uso comercial futuro do EVAonline
- ✅ Preferir: Domínio Público ou CC-BY (sem SA)

### ✅ Checklist para Avaliar Nova Fonte Climática

**ANTES de planejar implementação:**

1. ✅ **Acessar página de PRICING** (não apenas docs/features)
2. ✅ **Verificar tabela comparativa de tiers** (free vs paid)
3. ✅ **Confirmar variáveis específicas estão no free tier**
   - Não assumir que "available" = "free"
   - Procurar explicitamente: "evapotranspiration", "soil data", etc.
4. ✅ **Entender limites: mensal vs diário**
   - 1M/mês ≠ 1M/dia
   - Calcular uso real do projeto
5. ✅ **Ler termos de licença completos**
   - ShareAlike pode bloquear comercialização
   - Attribution pode ser aceitável
   - Non-commercial é dealbreaker
6. ✅ **Procurar "subscription required" ou "separate subscription"**
   - APIs podem ter múltiplos produtos com cobrança separada
7. ✅ **Verificar custos de upgrade**
   - Quanto custa tier seguinte?
   - É viável se projeto crescer?

### 🎯 Critérios Realistas para Projetos Acadêmicos

**Para EVAonline e projetos similares:**

| Critério | Aceitável | Problemático | Dealbreaker |
|----------|-----------|--------------|-------------|
| **Licença** | Domínio Público, CC-BY | CC-BY-SA (ShareAlike) | CC-BY-NC |
| **Custo** | $0/mês forever | $10-30/mês (pequeno) | $100+/mês |
| **ET/Soil** | Gratuito no free tier | Calculável de básicos | Só em paid |
| **Limite** | 1k+ calls/dia | 100-999 calls/dia | < 100/dia |
| **Período** | Diário ou ilimitado | Mensal com buffer | Mensal apertado |
| **Historical** | 5+ anos gratuito | 1-2 anos gratuito | Só recente |
| **Uptime** | 99%+ | 95-98% | < 95% |

### 📝 DECISÃO FINAL: Fontes Validadas EVAonline

**USAR (já implementadas, 100% gratuitas, sem restrições):**
1. ✅ **NASA POWER** (domínio público, global, 1981-presente, todas variáveis FAO-56)
2. ✅ **MET Norway** (CC-BY 4.0, Europa, tempo real, dados completos)
3. ✅ **NWS/NOAA** (domínio público, USA, official government data)

**NÃO ADICIONAR (custos/restrições proibitivas):**
1. ❌ OpenWeatherMap One Call 3.0 (subscription + ShareAlike licensing)
2. ❌ Visual Crossing (ET requer $150/mês Corporate plan)
3. ❌ WeatherAPI.com (ET e soil excluídos do free tier)

**ESTRATÉGIA FUTURA:**
- 📊 Focar em melhorar algoritmo de fusão com 3 fontes existentes
- 🔬 Validar cálculo FAO-56 com dados reais (Xavier dataset)
- 🌍 Potencialmente adicionar fontes regionais governamentais (INMET Brasil?)
- 💰 Se funding disponível no futuro: considerar Visual Crossing Corporate
- ❌ **NÃO adicionar** novas fontes comerciais (custos proibitivos)
- 📚 **Foco:** Melhorar algoritmo de fusão com fontes existentes

### Cenário Mundial On-Demand (queries usuário)

| Fonte | Limite Free | Estimativa Diária | Suficiente? |
|-------|-------------|-------------------|-------------|
| Visual Crossing | 1k rec/dia | ~500 queries x 10 dias = 5k rec | ⚠️ INSUFICIENTE (precisa cache + priorização) |
| OpenWeatherMap | 1k calls/dia | ~500 queries | ✅ SIM (com cache) |

**Conclusão:** Usar cache Redis agressivamente + priorizar Visual Crossing para MATOPIBA fixo!

---

## ✅ DECISÃO FINAL

### Implementar AGORA:
1. ✅ **Visual Crossing** - ETo direto, dados agrícolas, PRIORITÁRIO
2. ✅ **OpenWeatherMap** - Solar radiation detalhada, backup confiável

### Manter Atual:
- ✅ NASA POWER (domínio público global)
- ✅ MET Norway (Europa regional)
- ✅ NWS (USA regional)

### Remover/Restringir:
- ❌ **Open-Meteo** - Licença CC-BY-NC problemática
- ❌ **WeatherAPI.com** - Sem ET/soil no free tier (limitações críticas)

### Adicionar para Validação:
- ⚠️ ERA5 (opcional, complemento AgERA5)

---

**Autor:** GitHub Copilot  
**Data:** 08/10/2025  
**Próxima Ação:** Implementar Visual Crossing API client
