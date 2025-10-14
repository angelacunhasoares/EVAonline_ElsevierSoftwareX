# 🗺️ FLUXO COMPLETO: Heatmap MATOPIBA

## 📋 PASSO A PASSO - Do Backend ao Navegador

---

## 🔴 FASE 1: BACKEND - Preparação dos Dados

### 1.1 → Carregamento da Página (`app.py`)
```python
# frontend/app.py
@app.server.get("/matopiba")
async def matopiba_route(...):
    return templates.TemplateResponse("matopiba_map.html", context)
```

**O que acontece:**
- Usuário acessa `http://localhost:8000/matopiba`
- FastAPI serve template HTML

---

### 1.2 → Carregamento de Scripts JavaScript
```python
# frontend/app.py (linhas 139-145)
external_scripts=[
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',  # 1. Leaflet core
    '/assets/heatmap.js',                                # 2. h337 library
    '/assets/leaflet-heatmap.js',                        # 3. HeatmapOverlay plugin
    '/assets/matopiba-heatmap.js',                       # 4. Legacy integration
    '/assets/heatmap-callback.js'                        # 5. Dash callback (NOVO)
]
```

**O que acontece:**
- Navegador baixa scripts na ordem
- Console mostra: `✅ matopiba-heatmap.js carregado`
- Console mostra: `✅ heatmap-callback.js carregado (versão robusta)`

**✅ CHECKPOINT 1: Scripts carregados**

---

### 1.3 → Registro de Callbacks Clientside
```python
# frontend/app.py (linhas 331-344)
for day_key in ['today', 'tomorrow']:
    for var_key in ['eto_calculated', 'precipitation']:
        app.clientside_callback(
            "window.dash_clientside.matopiba.renderHeatmap",  # ← Função JavaScript
            Output(f'heatmap-trigger-{day_key}-{var_key}', 'children'),
            Input(f'heatmap-data-{day_key}-{var_key}', 'data')
            # SEM prevent_initial_call - permite render inicial
        )
```

**O que acontece:**
- Dash registra 4 callbacks (today/tomorrow × eto_calculated/precipitation)
- Callbacks ficam "escutando" mudanças em `heatmap-data-*` Stores
- Quando Store muda → chama `window.dash_clientside.matopiba.renderHeatmap()`

**✅ CHECKPOINT 2: Callbacks registrados**

---

## 🟠 FASE 2: GERAÇÃO DOS COMPONENTES

### 2.1 → Criação do Layout do Mapa
```python
# backend/core/map_results/matopiba_forecasts.py (linha ~520-560)
def _create_map_components(day_key, var_key, city_markers, values_for_scale, ...):
    
    # Preparar dados do heatmap
    heatmap_data = [
        {
            'lat': float(city['latitude']),
            'lng': float(city['longitude']),
            'value': normalize_value(city['value'])  # 0-1
        }
        for city in cities
    ]
    
    heatmap_config = {
        'data': heatmap_data,  # 337 pontos
        'config': {
            'radius': 25,
            'maxOpacity': 0.8,
            'minOpacity': 0.3,
            'blur': 0.75,
            'gradient': {
                '0.0': '#FFEDA0',  # Amarelo claro
                '0.5': '#FD8D3C',  # Laranja
                '1.0': '#BD0026'   # Vermelho escuro
            }
        },
        'max': 1.0
    }
    
    return html.Div([
        # 🔥 Store com dados (Input do callback)
        dcc.Store(
            id=f'heatmap-data-{day_key}-{var_key}',
            data=heatmap_config
        ),
        
        # 🎯 Div trigger (Output do callback)
        html.Div(
            id=f'heatmap-trigger-{day_key}-{var_key}',
            style={'display': 'none'}
        ),
        
        # 🗺️ Mapa Leaflet
        dl.Map(
            id=f"map-{day_key}-{var_key}",
            children=layers,  # Contorno MATOPIBA + marcadores
            center=[-10.5, -46.0],
            zoom=6
        ),
        
        # 📊 Resumo
        html.Div([summary_component])
    ])
```

**O que acontece:**
- Função cria componentes do mapa
- `dcc.Store` recebe objeto `heatmap_config` com 337 pontos
- `dl.Map` renderiza mapa Leaflet
- Store está **POPULADO** desde o início

**✅ CHECKPOINT 3: Componentes criados com dados**

---

## 🟡 FASE 3: RENDERIZAÇÃO NO NAVEGADOR

### 3.1 → Dash Renderiza Layout
```
NAVEGADOR recebe:
├── <div id="heatmap-data-today-eto_calculated"> (Store com dados)
├── <div id="heatmap-trigger-today-eto_calculated" style="display:none">
└── <div id="map-today-eto_calculated" class="leaflet-container">
```

**O que acontece:**
- HTML é injetado no DOM
- React (Dash) monta componentes
- Leaflet inicializa mapa

**⚠️ PROBLEMA POTENCIAL: Timing!**
- Dash pode disparar callback **ANTES** de Leaflet terminar inicialização
- Por isso precisamos do wait-for-ready pattern

---

### 3.2 → Dash Detecta Store Populado
```
Dash detecta:
  - Store heatmap-data-today-eto_calculated TEM DADOS
  - Callback registrado para esse Store
  - DISPARA callback automaticamente
```

**O que DEVERIA aparecer no console:**
```
🔥🔥🔥 CALLBACK HEATMAP DISPARADO!
✅ 337 pontos recebidos
📍 MapId: map-today-eto_calculated
```

**✅ CHECKPOINT 4: Callback disparado**

---

### 3.3 → Wait-for-Ready Pattern
```javascript
// heatmap-callback.js (linhas 35-77)
function waitAndRender(mapId, heatmapData, attempt) {
    // 1. Verifica elemento DOM
    const mapElement = document.getElementById(mapId);
    if (!mapElement) {
        console.log('⌛ Aguardando elemento do mapa...');
        setTimeout(() => waitAndRender(...), 500);
        return;
    }
    
    // 2. Verifica instância Leaflet
    const map = mapElement._leaflet_map;
    if (!map) {
        console.log('⌛ Aguardando instância Leaflet...');
        setTimeout(() => waitAndRender(...), 500);
        return;
    }
    
    // 3. Testa se mapa está REALMENTE pronto
    try {
        map.getCenter(); // Falha se não inicializado
        console.log('✅ Mapa está pronto!');
    } catch (e) {
        console.log('⌛ Mapa ainda não está pronto...');
        setTimeout(() => waitAndRender(...), 500);
        return;
    }
    
    // 4. Renderizar heatmap
    renderHeatmapNow(map, heatmapData);
}
```

**O que DEVERIA aparecer no console:**
```
⏱️ Tentativa 1/30...
⌛ Aguardando instância Leaflet...
⏱️ Tentativa 2/30...
⌛ Mapa ainda não está pronto...
⏱️ Tentativa 3/30...
✅ Mapa está pronto!
```

**✅ CHECKPOINT 5: Mapa pronto**

---

### 3.4 → Renderização do Heatmap
```javascript
// heatmap-callback.js (linhas 79-143)
function renderHeatmapNow(map, heatmapData) {
    // 1. Verificar biblioteca
    if (!window.HeatmapOverlay) {
        console.error('❌ HeatmapOverlay não disponível!');
        return;
    }
    console.log('✅ HeatmapOverlay disponível');
    
    // 2. Criar layer
    const heatmapLayer = new HeatmapOverlay({
        radius: 25,
        maxOpacity: 0.8,
        gradient: {...}
    });
    
    // 3. Adicionar ao mapa
    map.addLayer(heatmapLayer);
    
    // 4. Setar dados
    heatmapLayer.setData({
        max: 1.0,
        data: heatmapData.data  // 337 pontos
    });
    
    console.log('✅✅✅ HEATMAP CRIADO COM SUCESSO!');
    console.log(`📍 ${heatmapData.data.length} pontos renderizados`);
}
```

**O que DEVERIA aparecer no console:**
```
🎨 Renderizando heatmap...
✅ HeatmapOverlay disponível
⚙️ Config: {radius: 25, maxOpacity: 0.8, ...}
✅✅✅ HEATMAP CRIADO COM SUCESSO!
📍 337 pontos renderizados
```

**✅ CHECKPOINT 6: Heatmap renderizado**

---

## 🟢 FASE 4: RESULTADO VISUAL

### 4.1 → Camadas do Mapa
```
Mapa Leaflet final contém:
├── TileLayer (OpenStreetMap)
├── GeoJSON (Contorno MATOPIBA - linha vermelha)
├── CircleMarkers (337 cidades - pontos brancos)
└── HeatmapOverlay (Layer de calor - gradiente amarelo/laranja/vermelho)  ← ISSO!
```

**O que você DEVE VER:**
- 🗺️ Mapa base (ruas/satélite)
- 🔴 Contorno vermelho da região MATOPIBA
- ⚪ 337 pontos brancos (marcadores de cidades)
- 🔥 **Gradiente de calor amarelo/laranja/vermelho sobre o mapa**

---

## 🔍 DIAGNÓSTICO: O Que Está Faltando?

### Você vê no console:
```
✅ matopiba-heatmap.js carregado
✅ heatmap-callback.js carregado (versão robusta)
✅ heatmap-callback.js carregado (versão robusta)  ← duplicado
```

### Você NÃO vê:
```
🔥🔥🔥 CALLBACK HEATMAP DISPARADO!  ← FALTA!
```

---

## ❗ PROBLEMA IDENTIFICADO

**O callback NÃO está sendo disparado!**

Possíveis causas:

### 🔴 Causa 1: Callback não foi registrado corretamente
```python
# Verificar em app.py (linha ~331)
# Deve ter:
app.clientside_callback(
    "window.dash_clientside.matopiba.renderHeatmap",
    Output(f'heatmap-trigger-{day_key}-{var_key}', 'children'),
    Input(f'heatmap-data-{day_key}-{var_key}', 'data')
)
```

### 🔴 Causa 2: Store não está sendo populado
```python
# Verificar em matopiba_forecasts.py
# Deve ter:
dcc.Store(
    id=f'heatmap-data-{day_key}-{var_key}',
    data=heatmap_config  # ← DEVE TER DADOS!
)
```

### 🔴 Causa 3: IDs não batem
```
Store ID:   heatmap-data-today-eto_calculated
Callback:   Input('heatmap-data-today-eto_calculated', 'data')  ← DEVE SER IGUAL!
```

### 🔴 Causa 4: Namespace JavaScript não existe
```javascript
// Verificar se existe:
window.dash_clientside.matopiba.renderHeatmap
```

---

## 🛠️ PRÓXIMOS PASSOS DE DEBUG

Execute no **Console do navegador (F12)**:

```javascript
// 1. Verificar namespace
console.log('Namespace:', window.dash_clientside);
console.log('matopiba:', window.dash_clientside.matopiba);
console.log('renderHeatmap:', window.dash_clientside.matopiba.renderHeatmap);

// 2. Verificar Store
const store = document.getElementById('heatmap-data-today-eto_calculated');
console.log('Store element:', store);
console.log('Store props:', store ? store._dashprivate_layout : 'NOT FOUND');

// 3. Verificar dados no Store
if (store && store._dashprivate_layout && store._dashprivate_layout.props) {
    console.log('Store data:', store._dashprivate_layout.props.data);
}

// 4. Testar callback manualmente
if (window.dash_clientside.matopiba.renderHeatmap) {
    const testData = {
        data: [{lat: -10.5, lng: -46.0, value: 0.5}],
        config: {radius: 25, maxOpacity: 0.8},
        max: 1.0
    };
    window.dash_clientside.matopiba.renderHeatmap(testData);
}
```

---

## 📊 CHECKLIST DE VALIDAÇÃO

Execute cada item e responda SIM/NÃO:

- [ ] Scripts carregam sem erro 404?
- [ ] Console mostra mensagens de carregamento?
- [ ] `window.dash_clientside.matopiba` existe?
- [ ] `window.dash_clientside.matopiba.renderHeatmap` é uma função?
- [ ] Store `heatmap-data-today-eto_calculated` existe no DOM?
- [ ] Store tem propriedade `data` com 337 pontos?
- [ ] Map `map-today-eto_calculated` existe no DOM?
- [ ] `window.HeatmapOverlay` existe?
- [ ] Callback disparou (mensagem 🔥 no console)?
- [ ] Heatmap foi renderizado (mensagem ✅✅✅)?

---

## 📝 RESUMO DO FLUXO

```
BACKEND                           FRONTEND
┌─────────────────┐              ┌─────────────────┐
│ matopiba_       │              │ heatmap-        │
│ forecasts.py    │──────────────▶│ callback.js     │
│                 │   heatmap    │                 │
│ cria Store      │    config    │ renderHeatmap() │
│ com 337 pontos  │   (JSON)     │                 │
└─────────────────┘              └─────────────────┘
         │                                │
         │                                │
         ▼                                ▼
┌─────────────────┐              ┌─────────────────┐
│ dcc.Store       │              │ HeatmapOverlay  │
│ id=heatmap-data │──TRIGGER─────▶│ 337 pontos      │
│                 │   callback    │ amarelo/laranja │
│ data={...}      │              │ /vermelho       │
└─────────────────┘              └─────────────────┘
```

**Ponto de falha atual: TRIGGER não está acontecendo!**

---

## 🎯 AÇÃO IMEDIATA

Cole esses comandos no console e me envie o resultado:

```javascript
console.log('=== DEBUG HEATMAP ===');
console.log('1. Namespace:', typeof window.dash_clientside);
console.log('2. matopiba:', typeof window.dash_clientside?.matopiba);
console.log('3. renderHeatmap:', typeof window.dash_clientside?.matopiba?.renderHeatmap);
console.log('4. HeatmapOverlay:', typeof window.HeatmapOverlay);
console.log('5. Store existe?', !!document.getElementById('heatmap-data-today-eto_calculated'));
console.log('6. Map existe?', !!document.getElementById('map-today-eto_calculated'));
```

Com essas informações, conseguiremos identificar **EXATAMENTE** onde o fluxo está quebrando! 🎯
