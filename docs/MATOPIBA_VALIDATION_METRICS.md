## 📊 Métricas de Validação do MATOPIBA

### Visão Geral

O sistema EVAonline MATOPIBA implementa validação rigorosa do cálculo de ETo (Evapotranspiração de Referência) comparando os resultados do modelo EVAonline (Penman-Monteith FAO-56) com os valores de referência do Open-Meteo.

### Métricas Utilizadas

#### 1. **R² (Coeficiente de Determinação)**
- **Range**: 0 a 1
- **Interpretação**: Indica o quanto da variabilidade dos dados é explicada pelo modelo
- **Exemplo**: R² = 0.89 significa que 89% da variabilidade da ETo é explicada pelo modelo EVAonline

#### 2. **RMSE (Root Mean Square Error / Erro Quadrático Médio)**
- **Unidade**: mm/dia
- **Interpretação**: Representa o erro médio típico das estimativas
- **Exemplo**: RMSE = 0.45 mm/dia indica que o erro típico está em ±0.45 mm/dia

#### 3. **Bias (Viés Sistemático)**
- **Unidade**: mm/dia
- **Interpretação**: Mostra a tendência de superestimar (+) ou subestimar (-)
- **Exemplo**: 
  - Bias = +0.05 mm/dia → pequena superestimação
  - Bias = -0.15 mm/dia → pequena subestimação
  - Bias = 0.00 mm/dia → neutralidade perfeita

#### 4. **MAE (Mean Absolute Error / Erro Absoluto Médio)**
- **Unidade**: mm/dia
- **Interpretação**: Erro médio absoluto (sem considerar direção)
- **Uso**: Métrica complementar ao RMSE

---

### Critérios de Status Qualitativo

Os critérios de classificação são baseados em literatura científica reconhecida internacionalmente:

#### **Referências Científicas:**
1. **Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998)**  
   *"Crop evapotranspiration - Guidelines for computing crop water requirements"*  
   FAO Irrigation and Drainage Paper 56  
   🔗 [http://www.fao.org/3/x0490e/x0490e00.htm](http://www.fao.org/3/x0490e/x0490e00.htm)

2. **Popova, Z., Kercheva, M., Pereira, L.S. (2006)**  
   *"Validation of the FAO methodology for computing ETo with limited data"*  
   Agricultural Water Management, 81(3), 335-357

3. **Paredes, P., Pereira, L.S., Rodrigues, G.C., Botelho, N. (2018)**  
   *"Performance assessment of approaches for estimation of daily reference evapotranspiration"*  
   Agricultural Water Management, 201, 102-112

#### **Tabela de Classificação:**

| Status | R² | RMSE | Descrição |
|--------|----|----|-----------|
| ⭐ **EXCELENTE** | ≥ 0.90 | ≤ 0.5 mm/dia | Concordância muito alta - Uso recomendado para pesquisa e prática |
| 🟢 **MUITO BOM** | ≥ 0.85 | ≤ 0.8 mm/dia | Concordância alta - Adequado para uso operacional |
| 🟡 **BOM** | ≥ 0.75 | ≤ 1.2 mm/dia | Concordância adequada - Aceitável para estimativas gerais |
| 🟠 **ACEITÁVEL** | ≥ 0.65 | ≤ 1.5 mm/dia | Concordância moderada - Usar com cautela |
| 🔴 **INSUFICIENTE** | < 0.65 | > 1.5 mm/dia | Concordância baixa - Não recomendado |

**Nota**: Ambos os critérios (R² E RMSE) devem ser satisfeitos simultaneamente para alcançar determinado status.

---

### Validação no MATOPIBA

#### **Escopo da Validação:**
- **337 cidades** da região MATOPIBA (Maranhão, Tocantins, Piauí, Bahia)
- **2 dias** de previsão (hoje + amanhã)
- **Total**: 674 valores comparados (337 × 2)

#### **Metodologia:**
1. **Busca de dados**: Open-Meteo API fornece previsões meteorológicas + ETo FAO-56
2. **Cálculo EVAonline**: Pipeline completo (preprocessing → Penman-Monteith)
3. **Comparação**: ETo EVAonline vs ETo Open-Meteo
4. **Métricas globais**: Agregação de todas as 337 cidades

#### **Exemplo de Resultado:**
```yaml
Validação Global MATOPIBA (337 cidades)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
R²: 0.89          ⭐ EXCELENTE concordância
RMSE: 0.45 mm/dia ✓ Erro médio baixo
Bias: +0.05 mm/dia ✓ Pequena superestimação
MAE: 0.38 mm/dia  ✓ Erro absoluto baixo
Amostras: 674     (337 cidades × 2 dias)
```

---

### Por que NÃO validar Precipitação?

#### **Razões Técnicas:**

1. **Mesma Fonte de Dados**
   - Open-Meteo usa modelos de previsão numérica (GFS, ECMWF)
   - Não há dados observados independentes para validação
   - Validação seria circular (modelo vs modelo)

2. **Métricas Diferentes**
   - Precipitação requer métricas categóricas:
     - POD (Probability of Detection)
     - FAR (False Alarm Ratio)
     - CSI (Critical Success Index)
   - R² e RMSE são inadequados para eventos discretos (chuva sim/não)

3. **Necessidade de Dados Observados**
   - Validação de precipitação requer dados de estações meteorológicas
   - INMET, ANA, ou outras fontes de observação in-situ
   - Não disponível em tempo real para as 337 cidades

#### **Solução Implementada:**
- ✅ **ETo**: Validação completa com métricas científicas
- ℹ️ **Precipitação**: Apenas exibição dos valores previstos (sem validação)

---

### Implementação no Código

#### **Backend** (`eto_matopiba.py`):
```python
def calculate_validation_metrics(
    eto_evaonline: List[float],
    eto_openmeteo: List[float]
) -> Dict:
    """
    Calcula métricas baseadas em Allen et al. (1998) FAO-56.
    """
    # Cálculo de R², RMSE, Bias, MAE
    r2 = r2_score(om_clean, eva_clean)
    rmse = np.sqrt(mean_squared_error(om_clean, eva_clean))
    bias = np.mean(eva_clean - om_clean)
    mae = np.mean(np.abs(eva_clean - om_clean))
    
    # Classificação qualitativa baseada em literatura
    if r2 >= 0.90 and rmse <= 0.5:
        status = 'EXCELENTE'
    elif r2 >= 0.85 and rmse <= 0.8:
        status = 'MUITO BOM'
    # ...
```

#### **Frontend** (`matopiba_forecast_maps.py`):
```python
def create_validation_panel(validation: Dict) -> dbc.Card:
    """
    Painel de validação com métricas e explicações.
    Inclui referências científicas (FAO-56, Popova et al., Paredes et al.)
    """
    return dbc.Card([
        # Métricas em destaque (R², RMSE, Bias, Status)
        # Explicação detalhada de cada métrica
        # Referências científicas em rodapé
    ])
```

---

### Interface do Usuário

#### **Visualização no Mapa:**
- **Tooltip ao passar mouse**: Nome da cidade, estado, valor ETo/Precipitação
- **SEM métricas individuais** por cidade (evita poluição visual)

#### **Painel de Validação Global:**
```
📊 Validação Global: ETo EVAonline vs Open-Meteo (337 cidades)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    0.890            0.45           +0.05         ⭐ EXCELENTE
R² (Correlação)   RMSE (mm/dia)   Bias (mm/dia)   Status Geral
0-1: quanto mais  Erro médio:     +: superestima  337 cidades × 2 dias
próximo de 1,     quanto menor,   -: subestima
melhor            melhor

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 O que significam essas métricas?

• R² (Coeficiente de Determinação): Indica o quanto os valores se 
  correlacionam. R² = 0.890 significa que 89.0% da variabilidade 
  da ETo é explicada pelo modelo EVAonline.

• RMSE (Erro Quadrático Médio): Representa o erro médio das 
  estimativas. RMSE = 0.45 mm/dia indica que o erro típico está 
  nessa faixa.

• Bias (Viés Sistemático): Mostra a tendência de superestimar (+) 
  ou subestimar (-). Bias = +0.05 mm/dia indica superestimação 
  dos valores.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 Critérios baseados em:
Allen et al. (1998) FAO Irrigation and Drainage Paper 56
Popova et al. (2006) Validation of the FAO methodology
Paredes et al. (2018) Performance assessment of approaches for ETo estimation
```

---

### Conclusão

O sistema de validação implementado no EVAonline MATOPIBA:

✅ Usa métricas reconhecidas cientificamente  
✅ Baseia-se em literatura peer-reviewed (FAO-56)  
✅ Fornece classificação qualitativa objetiva  
✅ Explica as métricas de forma acessível  
✅ Valida apenas ETo (não precipitação - tecnicamente correto)  
✅ Agrega dados de 337 cidades para robustez estatística  

Isso garante transparência, credibilidade e usabilidade para usuários técnicos e não-técnicos.
