# frontend/src/maps.py
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import dash_leaflet as dl
import dash_leaflet.express as dlx
import geopandas as gpd
import pandas as pd
from dash import Dash
from loguru import logger

# O diretório base aponta para a raiz do projeto (3 níveis acima)
# Estrutura: raiz/backend/core/map_results/map_results.py -> raiz/
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

app = Dash()
app.layout = dl.Map(dl.TileLayer(), center=[56, 10], zoom=6, style={"height": "50vh"})


# Funções de estilo para as camadas base
def style_function_brasil(feature):
    return {"fillOpacity": 0, "color": "#505050", "weight": 1}


def style_function_matopiba(feature):
    return {"color": "#FF0000", "weight": 2.5, "fillOpacity": 0}


@lru_cache(maxsize=1)
def load_all_data():
    """Carrega dados geoespaciais: Brasil, MATOPIBA e cidades."""
    logger.info("Carregando dados geoespaciais (cacheado)...")
    try:
        brasil_gdf = gpd.read_file(
            BASE_DIR / "data" / "geojson" / "BR_UF_2024.geojson"
        )
        matopiba_gdf = gpd.read_file(
            BASE_DIR / "data" / "geojson" / "Matopiba_Perimetro.geojson"
        )
        cities_df = pd.read_csv(
            BASE_DIR / "data" / "csv" / "CITIES_MATOPIBA_337.csv",
            sep=","
        )
        
        # Converter para WGS84 (EPSG:4326) - padrão Leaflet
        for gdf in [brasil_gdf, matopiba_gdf]:
            gdf.to_crs(epsg=4326, inplace=True)
        
        logger.info("Dados geoespaciais carregados com sucesso.")
        return brasil_gdf, matopiba_gdf, cities_df
    except Exception as e:
        logger.error(f"Erro ao carregar dados geoespaciais: {e}")
        return None, None, None


def create_base_map_layers(t: Dict[str, str]):
    """Cria as camadas base (estados e contorno do MATOPIBA)."""
    brasil_gdf, matopiba_gdf, _ = load_all_data()
    
    if any(x is None for x in [brasil_gdf, matopiba_gdf]):
        logger.error("Falha ao carregar GeoDataFrames para o mapa base.")
        return []

    layers = [
        dl.GeoJSON(
            data=brasil_gdf.__geo_interface__,
            id="limites-estaduais",
            style=style_function_brasil,
            options={"name": t.get("state_borders", "State Borders")}
        ),
        dl.GeoJSON(
            data=matopiba_gdf.__geo_interface__,
            id="contorno-matopiba",
            style=style_function_matopiba,
            options={"name": t.get("matopiba_contour", "MATOPIBA Contour")}
        )
    ]
    return layers


def map_all_cities(t: Dict[str, str], heatmap_points=None):
    """Gera o mapa de todas as cidades do MATOPIBA com mapa de calor."""
    logger.info("Gerando mapa de todas as cidades do MATOPIBA")
    
    base_layers = create_base_map_layers(t)
    _, _, _, cities_df = load_all_data()

    # Gera pontos para o mapa de calor usando círculos (dash_leaflet não tem HeatMap)
    heatmap_points = heatmap_points if heatmap_points else [
        [row["LATITUDE"], row["LONGITUDE"], 1]  # Intensidade fixa de 1 por agora
        for _, row in cities_df.iterrows()
        if pd.notna(row["LATITUDE"]) and pd.notna(row["LONGITUDE"])
    ]
    city_markers = [
        dl.CircleMarker(
            center=[lat, lon],
            radius=5,
            color="red",
            fillColor="red",
            fillOpacity=0.6
        ) 
        for lat, lon, _ in heatmap_points
    ]
    heatmap_layer = dl.LayerGroup(city_markers, id="heatmap")

    map_obj = dl.LayerGroup(base_layers + [heatmap_layer])
    center = [-10, -55]
    zoom = 4
    map_desc = t.get("map_desc_matopiba", "Mapa ETo MATOPIBA")
    legend_html = f"""
    <div class="map-legend">
        <b>{t.get('legend', 'Legend')}</b><br>
        <span style="background: linear-gradient(to right, blue, green, yellow, orange, red); padding: 5px;">&nbsp;</span> {t.get('legend_heatmap', 'City Density')}<br>
        <span style="color: red; font-size: 16px;">━</span> {t.get('perimeter', 'Perimeter')}<br>
        <b>{t.get('source', 'Source')}:</b> {t.get('map_source_all_cities', 'MATOPIBA Data')}
    </div>
    """
    return map_obj, center, zoom, map_desc, legend_html


def create_interactive_map(t: Dict[str, str], heatmap_points=None):
    """Gera o mapa global interativo para seleção de coordenadas."""
    logger.info("Gerando mapa global interativo")
    
    base_layers = create_base_map_layers(t)
    heatmap_points = heatmap_points if heatmap_points else []  # Sem pontos iniciais para foco em interação

    heatmap_layer = dl.HeatMap(
        id="heatmap",
        points=heatmap_points,
        radius=25,
        blur=15,
        gradient={0.2: "blue", 0.4: "green", 0.6: "yellow", 0.8: "orange", 1.0: "red"}
    )

    map_obj = dl.LayerGroup(base_layers + [heatmap_layer])
    center = [-15, -47]  # Centro aproximado do Brasil
    zoom = 4
    map_desc = t.get("map_desc_global", "Mapa Global")
    legend_html = f"""
    <div class="map-legend">
        <b>{t.get('legend', 'Legend')}</b><br>
        <span style="background: linear-gradient(to right, blue, green, yellow, orange, red); padding: 5px;">&nbsp;</span> {t.get('legend_heatmap', 'City Density')}<br>
        <i class="fa fa-globe" style="color: blue;"></i> {t.get('legend_map4_global', 'Interactive Global Map')}<br>
    </div>
    """
    return map_obj, center, zoom, map_desc, legend_html


def create_matopiba_real_map():
    """
    Cria mapa interativo da região MATOPIBA com dados reais.
    
    Retorna um componente html.Div contendo:
    - Mapa Leaflet com limites do Brasil
    - Contorno da região MATOPIBA (vermelho)
    - 337 cidades como marcadores circulares
    
    Returns:
        html.Div: Componente Dash com o mapa MATOPIBA
    """
    from dash import html
    
    logger.info("Criando mapa MATOPIBA com dados reais")
    
    try:
        # Carregar dados geoespaciais
        brasil_gdf, matopiba_gdf, cities_df = load_all_data()
        
        if any(x is None for x in [brasil_gdf, matopiba_gdf, cities_df]):
            logger.error("Falha ao carregar dados para mapa MATOPIBA")
            return html.Div([
                html.P(
                    "⚠️ Erro ao carregar dados do mapa MATOPIBA. "
                    "Verifique os arquivos GeoJSON e CSV.",
                    className="text-danger text-center p-4"
                )
            ])
        
        # Criar camadas do mapa
        layers = [
            # Camada base do OpenStreetMap
            dl.TileLayer(),
            
            # Limites dos estados do Brasil (cinza)
            dl.GeoJSON(
                data=json.loads(brasil_gdf.to_json()),
                id="limites-brasil-matopiba",
                style={"fillOpacity": 0, "color": "#505050", "weight": 1},
                options={"attribution": "IBGE"}
            ),
            
            # Contorno da região MATOPIBA (vermelho)
            dl.GeoJSON(
                data=json.loads(matopiba_gdf.to_json()),
                id="contorno-matopiba-map",
                style={"color": "#FF0000", "weight": 2.5, "fillOpacity": 0},
                options={"attribution": "MATOPIBA"}
            ),
        ]
        
        # Adicionar marcadores das 337 cidades
        city_markers = []
        for _, row in cities_df.iterrows():
            if pd.notna(row["LATITUDE"]) and pd.notna(row["LONGITUDE"]):
                city_markers.append(
                    dl.CircleMarker(
                        center=[row["LATITUDE"], row["LONGITUDE"]],
                        radius=4,
                        color="#dc3545",
                        fillColor="#dc3545",
                        fillOpacity=0.6,
                        weight=1,
                        children=[
                            dl.Popup(
                                html.Div([
                                    html.Strong(
                                        row.get("CITY", "Cidade"),
                                        style={"fontSize": "13px"}
                                    ),
                                    html.Br(),
                                    html.Small(
                                        f"Lat: {row['LATITUDE']:.4f}, "
                                        f"Lon: {row['LONGITUDE']:.4f}",
                                        className="text-muted"
                                    )
                                ])
                            )
                        ]
                    )
                )
        
        # Adicionar layer group com todas as cidades
        if city_markers:
            layers.append(
                dl.LayerGroup(city_markers, id="cidades-matopiba")
            )
        
        # Criar mapa Leaflet
        matopiba_map = html.Div([
            html.P(
                "Região MATOPIBA (Maranhão, Tocantins, Piauí, Bahia) "
                "com 337 cidades mapeadas.",
                className="mb-3 text-muted",
                style={"fontSize": "14px"}
            ),
            dl.Map(
                children=layers,
                center=[-10, -47],  # Centro da região MATOPIBA
                zoom=5,
                style={
                    'width': '100%',
                    'height': '500px',
                    'borderRadius': '8px',
                    'border': '1px solid #dee2e6'
                },
                id="matopiba-leaflet-map"
            ),
            html.Div([
                html.Small([
                    html.I(className="fas fa-map-marker-alt text-danger me-1"),
                    f"{len(city_markers)} cidades mapeadas"
                ], className="text-muted me-3"),
                html.Small([
                    html.I(className="fas fa-border-all text-secondary me-1"),
                    "Limites estaduais (IBGE)"
                ], className="text-muted me-3"),
                html.Small([
                    html.I(className="fas fa-draw-polygon text-danger me-1"),
                    "Contorno MATOPIBA"
                ], className="text-muted")
            ], className="mt-2 d-flex justify-content-center",
               style={"fontSize": "12px"})
        ], className="p-3")
        
        logger.info(
            f"Mapa MATOPIBA criado com sucesso: "
            f"{len(city_markers)} cidades"
        )
        return matopiba_map
        
    except Exception as e:
        logger.error(f"Erro ao criar mapa MATOPIBA: {e}")
        return html.Div([
            html.P(
                f"⚠️ Erro ao criar mapa MATOPIBA: {str(e)}",
                className="text-danger text-center p-4"
            )
        ])


def create_world_real_map():
    """
    Cria mapa mundial interativo com geolocalização, favoritos e ações rápidas.
    
    Retorna um componente html.Div contendo:
    - Mapa Leaflet mundial interativo
    - Sistema de geolocalização
    - Painel de ações rápidas
    - Sistema de favoritos com paginação
    - Instruções colapsáveis
    
    Returns:
        html.Div: Componente Dash com o mapa mundial completo
    """
    import dash_bootstrap_components as dbc
    import dash_leaflet as dl
    from dash import dcc, html
    
    logger.info("Criando mapa mundial interativo")
    
    return html.Div([
        # Componente de geolocalização
        dcc.Geolocation(
            id='geolocation',
            update_now=False,
            high_accuracy=True,
            maximum_age=0,
            timeout=10000,
            show_alert=True
        ),

        # Barra de ferramentas compacta (info + ações alinhados horizontalmente)
        dbc.Row([
            dbc.Col([
                # Informações do local
                html.Div(id='click-info', 
                        className="small",
                        style={'display': 'flex',
                               'alignItems': 'center',
                               'justifyContent': 'flex-start'})
            ], md=8, sm=12),
            
            dbc.Col([
                # Painel de ações rápidas (sem título separado)
                html.Div([
                    html.Span([
                        html.I(className="fas fa-bolt me-1", 
                               style={"fontSize": "12px"}),
                        html.Strong("Ações Rápidas:", 
                                   style={"fontSize": "12px"})
                    ], className="text-muted me-2"),
                    html.Div(id='quick-actions-panel', 
                            children=[
                                dbc.Button(
                                    [html.I(className="fas fa-location-arrow")],
                                    id="get-location-btn",
                                    color="success",
                                    size="sm",
                                    outline=True,
                                    title="Obter Minha Localização",
                                    className="me-1"
                                )
                            ], 
                            className="d-inline-flex gap-1")
                ], style={'display': 'flex', 
                         'alignItems': 'center',
                         'justifyContent': 'flex-end'})
            ], md=4, sm=12)
        ], className="mb-1 align-items-center"),
        
        # Modal para resultados de cálculos
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
            dbc.ModalBody(id="modal-body"),
            dbc.ModalFooter(
                dbc.Button("Fechar", id="close-modal", className="ms-auto")
            ),
        ], id="result-modal", size="lg", is_open=False),

        # Mapa Leaflet
        dl.Map(
            id="map",
            children=[dl.TileLayer()],
            center=[20, 0],
            zoom=2,
            minZoom=2,
            maxBounds=[[-90, -180], [90, 180]],
            maxBoundsViscosity=1.0,
            style={
                'width': '100%',
                'height': '500px',
                'cursor': 'pointer',
                'position': 'relative',
                'zIndex': 1
            },
            dragging=True,
            scrollWheelZoom=True,
            doubleClickZoom=True,
            boxZoom=True,
            keyboard=True,
            markerZoomAnimation=True
        ),

        # Aviso de erro de geolocalização (compacto, acima da legenda)
        html.Div(id='geolocation-error-msg', className="mt-3 mb-2"),

        # Instruções colapsáveis (Accordion)
        html.Div([
            dbc.Accordion([
                dbc.AccordionItem([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-location-dot me-2",
                                  style={"color": "#dc3545", "fontSize": "16px"}),
                            html.Span("Sua localização", 
                                     style={"fontSize": "13px", "fontWeight": "500"}),
                        ], className="d-flex align-items-center mb-2"),
                        html.Small(
                            "Clique no botão de localização para marcar sua posição",
                            className="text-muted d-block ms-4 mb-3",
                            style={"fontSize": "12px"}
                        ),
                        
                        html.Div([
                            html.I(className="fas fa-map-pin me-2",
                                  style={"color": "#0d6efd", "fontSize": "16px"}),
                            html.Span("Pontos de interesse", 
                                     style={"fontSize": "13px", "fontWeight": "500"}),
                        ], className="d-flex align-items-center mb-2"),
                        html.Small(
                            "Clique em qualquer local do mapa para adicionar até 9 pontos",
                            className="text-muted d-block ms-4 mb-3",
                            style={"fontSize": "12px"}
                        ),
                        
                        html.Div([
                            html.I(className="fas fa-star me-2",
                                  style={"color": "#ffc107", "fontSize": "16px"}),
                            html.Span("Favoritos", 
                                     style={"fontSize": "13px", "fontWeight": "500"}),
                        ], className="d-flex align-items-center mb-2"),
                        html.Small(
                            "Salve até 20 localizações favoritas para acesso rápido",
                            className="text-muted d-block ms-4",
                            style={"fontSize": "12px"}
                        ),
                    ])
                ], title=[
                    html.I(className="fas fa-info-circle me-2", 
                          style={"color": "#2d5016"}),
                    html.Span("Como usar o mapa", 
                             style={"color": "#2d5016", "fontSize": "14px", "fontWeight": "600"})
                ])
            ], start_collapsed=True, flush=True, className="shadow-sm mb-3"),
            
            # Seção de favoritos com paginação (Accordion colapsável)
            dbc.Accordion([
                dbc.AccordionItem([
                    # Controles de paginação superiores
                    html.Div([
                        html.Div([
                            html.Label("Itens por página:", 
                                      className="me-2 small text-muted",
                                      style={"fontSize": "11px"}),
                            dcc.Dropdown(
                                id="favorites-page-size",
                                options=[
                                    {"label": "5", "value": 5},
                                    {"label": "10", "value": 10},
                                    {"label": "20", "value": 20}
                                ],
                                value=5,
                                clearable=False,
                                style={"width": "70px", "fontSize": "12px"}
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-trash-alt me-1"),
                                 html.Span("Limpar Tudo", 
                                          style={"fontSize": "11px"})],
                                id="clear-all-favorites-btn",
                                color="danger",
                                size="sm",
                                outline=True,
                                style={"fontSize": "11px", 
                                       "padding": "0.25rem 0.5rem",
                                       "marginLeft": "auto"}
                            )
                        ], className="d-flex align-items-center mb-2")
                    ]),
                    # Lista de favoritos
                    html.Div(id="favorites-list", className="small"),
                    # Controles de navegação de páginas (sempre renderizados, mas ocultos quando não necessários)
                    html.Div([
                        dbc.Button(
                            [html.I(className="fas fa-chevron-left me-1"), "Anterior"],
                            id="favorites-prev-page",
                            color="primary",
                            outline=True,
                            size="sm",
                            className="me-2",
                            style={"fontSize": "11px"}
                        ),
                        html.Span(id="favorites-pagination-info", className="mx-2 small"),
                        dbc.Button(
                            ["Próxima", html.I(className="fas fa-chevron-right ms-1")],
                            id="favorites-next-page",
                            color="primary",
                            outline=True,
                            size="sm",
                            className="ms-2",
                            style={"fontSize": "11px"}
                        )
                    ], id="favorites-pagination", className="mt-2 d-flex justify-content-center align-items-center")
                ], title=[
                    html.I(className="fas fa-star text-warning me-2"),
                    html.Span("Favoritos ", 
                             style={"fontSize": "14px", "fontWeight": "600"}),
                    dbc.Badge(id="favorites-count", 
                             color="primary", 
                             className="ms-2",
                             style={"fontSize": "11px"})
                ])
            ], start_collapsed=True, flush=True, className="shadow-sm mb-3"),
            
            # Modal de confirmação para limpar favoritos
            dbc.Modal([
                dbc.ModalHeader(
                    dbc.ModalTitle([
                        html.I(className="fas fa-exclamation-triangle "
                                        "text-warning me-2"),
                        "Confirmar Exclusão"
                    ])
                ),
                dbc.ModalBody([
                    html.P([
                        "Tem certeza que deseja ",
                        html.Strong("excluir TODOS os favoritos", 
                                   style={"color": "#dc3545"}),
                        "?"
                    ], className="mb-2"),
                    html.P([
                        html.I(className="fas fa-info-circle me-2 text-info"),
                        html.Span(id="clear-favorites-count", 
                                 className="text-muted small")
                    ], className="mb-0")
                ]),
                dbc.ModalFooter([
                    dbc.Button(
                        "Cancelar",
                        id="cancel-clear-favorites",
                        color="secondary",
                        outline=True,
                        size="sm"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-trash-alt me-2"),
                         "Sim, Excluir Tudo"],
                        id="confirm-clear-favorites",
                        color="danger",
                        size="sm"
                    )
                ])
            ], id="clear-favorites-modal", is_open=False, centered=True),
            
            # Stores para paginação
            dcc.Store(id='favorites-current-page', data=1)
        ], className="mt-3")
    ], className="p-3")
