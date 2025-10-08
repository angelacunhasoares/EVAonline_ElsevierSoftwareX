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


def map_piracicaba_city(t: Dict[str, str], heatmap_points=None):
    """Gera o mapa da cidade de Piracicaba com mapa de calor."""
    logger.info("Gerando mapa da cidade de Piracicaba")
    
    base_layers = create_base_map_layers(t)
    _, _, _, cities_df = load_all_data()
    piracicaba_data = cities_df[cities_df['CITY'].str.contains('Piracicaba', case=False, na=False)]
    heatmap_points = heatmap_points if heatmap_points else [
        [row["LATITUDE"], row["LONGITUDE"], 1]
        for _, row in piracicaba_data.iterrows()
        if pd.notna(row["LATITUDE"]) and pd.notna(row["LONGITUDE"])
    ]
    city_markers = [
        dl.CircleMarker(
            center=[lat, lon],
            radius=3,  # Menor raio para detalhe em escala local
            color="red",
            fillColor="red",
            fillOpacity=0.8
        ) 
        for lat, lon, _ in heatmap_points
    ]
    heatmap_layer = dl.LayerGroup(city_markers, id="heatmap")

    map_obj = dl.LayerGroup(base_layers + [heatmap_layer])
    center = [-22.725, -47.649]
    zoom = 10
    map_desc = t.get("map_desc_piracicaba", "Piracicaba, SP Brasil")
    legend_html = f"""
    <div class="map-legend">
        <b>{t.get('legend', 'Legend')}</b><br>
        <span style="background: linear-gradient(to right, blue, green, yellow, orange, red); padding: 5px;">&nbsp;</span> {t.get('legend_heatmap', 'City Density')}<br>
        <span style="color: red; font-size: 16px;">━</span> {t.get('legend_map2_perimeter', 'City Perimeter')}<br>
        <b>{t.get('source', 'Source')}:</b> IBGE (Perimeter)
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
