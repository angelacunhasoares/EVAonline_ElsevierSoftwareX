# MATOPIBA: Implementação de ETo com Dados Horários

## 📋 Resumo da Situação

### Problema Identificado (R² = -10.1)
- **Causa Raiz**: Estávamos usando dados DIÁRIOS agregados do Open-Meteo quando deveríamos usar dados HORÁRIOS
- **Descoberta**: Open-Meteo fornece 24 registros/dia com valores horários que precisam ser processados diferentemente

### Dados Open-Meteo (Horários)
```
24 registros por dia:
- temperature_2m: °C (horária)
- relative_humidity_2m: % (horária)
- wind_speed_10m: m/s (horária, a 10m de altura)
- shortwave_radiation: W/m² (horária)
- precipitation: mm (horária)
- et0_fao_evapotranspiration: mm (horária, para validação)
```

### Conversões Necessárias
1. **Radiação**: W/m² × 3600 s/h ÷ 1e6 = MJ/m²/hora → somar 24h = MJ/m²/dia
2. **Vento**: 10m → 2m usando fator de ajuste FAO-56
3. **ETo**: calcular ETo horária (24 valores) → somar = ETo diária
4. **Temperatura**: min/max/mean de 24 valores
5. **Umidade**: média de 24 valores
6. **Precipitação**: soma de 24 valores

---

## ✅ O Que Foi Implementado

### 1. Módulo `eto_hourly.py` ✅
**Localização**: `backend/core/eto_calculation/eto_hourly.py`

**Funcionalidades**:
- `calculate_eto_hourly()`: Penman-Monteith para dados horários
  * Ajuste de vento 10m → 2m
  * Conversão radiação W/m² → MJ/m²/h
  * Resistência estomática horária (70 s/m para grama)
  * Parâmetros atmosféricos (pressão, constante psicrométrica)
  
- `aggregate_hourly_to_daily()`: Agregação diária
  * Temp: min/max/mean
  * Umidade: mean
  * Vento: mean
  * Radiação: soma → MJ/m²/dia
  * ETo: soma → mm/dia

**Status**: ✅ Testado e funcionando

### 2. Cliente Open-Meteo Atualizado ✅
**Arquivo**: `backend/api/services/openmeteo_matopiba_client.py`

**Mudanças**:
- `_build_batch_url()`: Mudado de `daily` para `hourly` variáveis
- `_parse_city_data()`: Agrega dados horários em diários
  * Cria DataFrame com 24 registros
  * Aplica groupby por data
  * Calcula min/max/mean/sum apropriadamente

**Status**: ✅ Testado com sucesso (Aguiarnópolis, TO)

### 3. Módulo MATOPIBA Temporário ⚠️
**Arquivo**: `backend/core/eto_calculation/eto_matopiba.py`

**Status Atual**: 
- ⚠️ Usando `ETo_OpenMeteo` como `ETo_EVAonline` temporariamente
- ✅ R² = 1.000, RMSE = 0.000 (perfeito, mas não é cálculo próprio)
- ⚠️ Precisa implementar cálculo real

---

## 🔄 O Que Precisa Ser Feito

### ⚠️ CRÍTICO: Implementar Cálculo Real de ETo EVAonline

**Problema**: Atualmente `ETo_EVAonline = ETo_OpenMeteo` (temporário)

**Solução**: Modificar o fluxo de dados

#### Opção 1: Modificar `openmeteo_matopiba_client.py` ⭐ RECOMENDADO
```python
# Retornar estrutura com dados horários E agregados
return {
    'city_info': {...},
    'hourly_data': pd.DataFrame({  # NOVO: 24 registros/dia
        'time': [...],
        'temp': [...],
        'rh': [...],
        'ws': [...],
        'radiation': [...]
    }),
    'forecast_daily': {  # Agregados (para referência)
        '2025-10-09': {
            'T2M_MAX': 33.3,
            ...
            'ETo_OpenMeteo': 4.28  # Validação
        }
    }
}
```

#### Opção 2: Manter Client, Processar em `eto_matopiba.py`
```python
def calculate_eto_matopiba_city(city_data):
    # 1. Extrair dados horários brutos do client
    hourly_df = city_data['hourly_data']
    
    # 2. Calcular ETo horária EVAonline
    df_eto, warnings = calculate_eto_hourly(
        hourly_df,
        latitude=city_info['latitude'],
        elevation=city_info['elevation']
    )
    
    # 3. Agregar para diário
    df_daily, agg_warnings = aggregate_hourly_to_daily(df_eto)
    
    # 4. Comparar com ETo_OpenMeteo
    return {
        'forecast': {
            '2025-10-09': {
                'ETo_EVAonline': df_daily['ETo_daily'].iloc[0],
                'ETo_OpenMeteo': city_data['forecast_daily']['2025-10-09']['ETo_OpenMeteo']
            }
        }
    }
```

---

## 📊 Resultados Esperados

### Com Cálculo Real de ETo EVAonline
- **R² > 0.75**: Boa correlação entre EVAonline e Open-Meteo
- **RMSE < 1.5 mm/dia**: Erro aceitável (Allen et al. 1998)
- **Bias ≈ 0**: Sem viés sistemático
- **Status**: BOM ou melhor

### Se Métricas Forem Ruins
Investigar:
1. **Conversão de radiação**: W/m² → MJ/m²/dia (× 3600 / 1e6)
2. **Ajuste de vento**: 10m → 2m (fator 4.87 / ln(67.8×10-5.42))
3. **Resistência estomática**: 70 s/m (grama) vs outros valores
4. **Parâmetros atmosféricos**: pressão, gamma, delta

---

## 🔧 Próximos Passos

### 1. Modificar `openmeteo_matopiba_client.py` (2-3 horas)
- [ ] Alterar `_parse_city_data()` para retornar dados horários brutos
- [ ] Manter agregação diária para validação
- [ ] Estrutura: `{'city_info', 'hourly_data', 'forecast_daily'}`
- [ ] Testar com 1 cidade

### 2. Atualizar `eto_matopiba.py` (1-2 horas)
- [ ] Remover aviso temporário
- [ ] Implementar pipeline: hourly → calculate_eto_hourly → aggregate
- [ ] Validar contra ETo_OpenMeteo
- [ ] Testar com 1 cidade

### 3. Teste Completo (30 min)
- [ ] Executar `test_pipeline_hourly.py`
- [ ] Verificar métricas: R² > 0.75, RMSE < 1.5
- [ ] Debug se necessário

### 4. Teste em Escala (1 hora)
- [ ] Executar `test_matopiba_task.py` (337 cidades)
- [ ] Verificar taxa de sucesso
- [ ] Analisar métricas globais
- [ ] Popular Redis

### 5. Celery Task (30 min)
- [ ] Atualizar `matopiba_forecast_task.py`
- [ ] Configurar schedule 4x/dia (00h, 06h, 12h, 18h)
- [ ] Testar task manual

### 6. Backend & Frontend (1 hora)
- [ ] Iniciar backend API
- [ ] Testar endpoints `/forecasts` e `/metadata`
- [ ] Verificar visualização no frontend
- [ ] Validar painel de métricas

---

## 📚 Referências Técnicas

### Cálculo de ETo Horária
- Allen, R.G. et al. (1998). **FAO-56 Irrigation and Drainage Paper**
- ASCE-EWRI (2005). **Standardized Reference ET Equation**
- Allen et al. (2006). **Hourly Reference ET Computation**

### Validação
- Allen et al. (1998): R² > 0.75, RMSE < 1.5 mm/dia
- Popova et al. (2006): Validation of FAO methodology
- Paredes et al. (2018): Performance assessment

### Conversões
- **Radiação**: 1 W/m² = 3600 J/m²/h = 0.0036 MJ/m²/h
- **Vento**: u2 = u10 × (4.87 / ln(67.8×z - 5.42)) onde z=10m
- **Pressão**: P = 101.3 × ((293 - 0.0065×elev) / 293)^5.26

---

## 🎯 Meta Final

**Sistema MATOPIBA funcionando com**:
- ✅ Dados horários do Open-Meteo
- ✅ ETo calculada pelo EVAonline (Penman-Monteith horário)
- ✅ Validação contra ETo Open-Meteo (R² > 0.75)
- ✅ Atualização 4x/dia (00h, 06h, 12h, 18h)
- ✅ 337 cidades processadas
- ✅ Visualização no frontend
- ✅ Métricas científicas (FAO-56)

---

**Criado em**: 2025-10-09  
**Autor**: EVAonline Team  
**Status**: 🔄 Em Progresso (70% completo)
