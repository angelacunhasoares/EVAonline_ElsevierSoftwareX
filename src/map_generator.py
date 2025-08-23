# frontend/src/maps.py
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any
import dash_leaflet as dl
import dash_leaflet.express as dlx
from dash import Dash
import geopandas as gpd
import pandas as pd
from loguru import logger

# O diretório base é definido de forma explícita.
BASE_DIR = Path(__file__).resolve().parent.parent

app = Dash()
app.layout = dl.Map(dl.TileLayer(), center=[56, 10], zoom=6, style={"height": "50vh"})


# Funções de estilo para as camadas base
def style_function_brasil(feature):
    return {"fillOpacity": 0, "color": "#505050", "weight": 1}


def style_function_matopiba(feature):
    return {"color": "#FF0000", "weight": 2.5, "fillOpacity": 0}


def normalize_text(text):
    """Normaliza o texto para correspondência de chaves."""
    if not isinstance(text, str):
        return ""
    text = text.lower().replace("º", " ").replace("°", " ")
    text = text.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c")
    text = text.replace("â", "a").replace("ê", "e")
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# Dicionário de cores para cada tipo de clima
color_map = {
    'Equatorial, quente - média > 18° C em todos os meses, super-úmido sem seca': '#6A339A', 
    'Equatorial, quente - média > 18° C em todos os meses, super-úmido subseca': '#A378B9', 
    'Equatorial, quente - média > 18° C em todos os meses, úmido 1 a 2 meses secos': '#D1AAD1', 
    'Equatorial, quente - média > 18° C em todos os meses, úmido 3 meses secos': '#E6D4E6', 
    'Equatorial, subquente - média entre 15 e 18 ° C em pelo menos 1 mês, super-úmido subseca': '#00A651', 
    'Equatorial, subquente - média entre 15 e 18 ° C em pelo menos 1 mês, úmido 1 a 2 meses secos': '#8BC53F', 
    'Equatorial, subquente - média entre 15 e 18 ° C em pelo menos 1 mês, úmido 3 meses secos': '#B5D69C', 
    "Massa d'água": '#aadaff', 'Temperado, mesotérmico brando - média entre 10 e 15° C, super-úmido sem seca': '#00AEEF', 
    'Temperado, mesotérmico brando - média entre 10 e 15° C, super-úmido subseca': '#66C5EE', 
    'Temperado, mesotérmico mediano - média > 10° C, super-úmido subseca': '#B3B3B3', 
    'Temperado, subquente - média entre 15 e 18 ° C em pelo menos 1 mês, super-úmido sem seca': '#00843D', 
    'Temperado, subquente - média entre 15 e 18 ° C em pelo menos 1 mês, super-úmido subseca': '#00A651', 
    'Tropical Brasil Central, mesotérmico brando - média entre 10 e 15° C, semi-úmido 4 a 5 meses': '#E6F5FB', 
    'Tropical Brasil Central, mesotérmico brando - média entre 10 e 15° C, super-úmido sem seca': '#00AEEF', 
    'Tropical Brasil Central, mesotérmico brando - média entre 10 e 15° C, super-úmido subseca': '#66C5EE', 
    'Tropical Brasil Central, mesotérmico brando - média entre 10 e 15° C, úmido 1 a 2 meses secos': '#99D9F2', 
    'Tropical Brasil Central, mesotérmico brando - média entre 10 e 15° C, úmido 3 meses secos': '#CCEBF7', 
    'Tropical Brasil Central, mesotérmico mediano - média > 10° C, super-úmido sem seca': '#808080', 
    'Tropical Brasil Central, mesotérmico mediano - média > 10° C, úmido 1 a 2 meses secos': '#D9D9D9', 
    'Tropical Brasil Central, quente - média > 18° C em todos os meses, semi-árido 6 meses secos': '#FFFFBE', 
    'Tropical Brasil Central, quente - média > 18° C em todos os meses, semi-árido 7 a 8 meses secos': '#FFFF00', 
    'Tropical Brasil Central, quente - média > 18° C em todos os meses, semi-árido 9 a 10 meses secos': '#F7941D', 
    'Tropical Brasil Central, quente - média > 18° C em todos os meses, semi-úmido 4 a 5 meses secos': '#F2EFF2', 
    'Tropical Brasil Central, quente - média > 18° C em todos os meses, super-úmido sem seca': '#6A339A', 
    'Tropical Brasil Central, quente - média > 18° C em todos os meses, super-úmido subseca': '#A378B9', 
    'Tropical Brasil Central, quente - média > 18° C em todos os meses, úmido 1 a 2 meses secos': '#D1AAD1', 
    'Tropical Brasil Central, quente - média > 18° C em todos os meses, úmido 3 meses secos': '#E6D4E6', 
    'Tropical Brasil Central, subquente - média entre 15 e 18 ° C em pelo menos 1 mês, semi-árido 6 meses secos': '#EFF6E9', 
    'Tropical Brasil Central, subquente - média entre 15 e 18 ° C em pelo menos 1 mês, semi-úmido 4 a 5 meses secos': '#D9EAD3', 
    'Tropical Brasil Central, subquente - média entre 15 e 18 ° C em pelo menos 1 mês, úmido 1 a 2 meses secos': '#8BC53F', 
    'Tropical Brasil Central, subquente - média entre 15 e 18 ° C em pelo menos 1 mês, úmido 3 meses secos': '#B5D69C', 
    'Tropical Brasil Central, subquente - média entre 15 e 18º C em pelo menos 1 mês, super-úmido sem seca': '#00843D', 
    'Tropical Brasil Central, subquente - média entre 15 e 18º C em pelo menos 1 mês, super-úmido subseca': '#00A651', 
    'Tropical Nordeste Oriental, quente - média > 18 ° C em todos os meses, semi-úmido 4 a 5 meses secos': '#F2EFF2', 
    'Tropical Nordeste Oriental, quente - média > 18° C em todos os meses, semi-árido 6 meses secos': '#FFFFBE', 
    'Tropical Nordeste Oriental, quente - média > 18° C em todos os meses, semi-árido 7 a 8 meses secos': '#FFFF00', 
    'Tropical Nordeste Oriental, quente - média > 18° C em todos os meses, semi-árido 9 a 10 meses secos': '#F7941D', 
    'Tropical Nordeste Oriental, quente - média > 18° C em todos os meses, super-úmido sem seca': '#6A339A', 
    'Tropical Nordeste Oriental, quente - média > 18° C em todos os meses, super-úmido subseca': '#A378B9', 
    'Tropical Nordeste Oriental, quente - média > 18° C em todos os meses, úmido 3 meses secos': '#E6D4E6', 
    'Tropical Nordeste Oriental, quente - média > 18º C em todos os meses, úmido 1 a 2 meses secos': '#D1AAD1', 
    'Tropical Nordeste Oriental, subquente - média entre 15 e 18 ° C em pelo menos 1 mês, semi-úmido 4 a 5 meses secos': '#D9EAD3', 
    'Tropical Nordeste Oriental, subquente - média entre 15 e 18º C em pelo menos 1 mês, úmido 3 meses secos': '#B5D69C', 
    'Tropical Zona Equatorial, quente - média > 18° C em todos os meses, semi-árido 11 meses secos': '#ED1C24', 
    'Tropical Zona Equatorial, quente - média > 18° C em todos os meses, semi-árido 6 meses secos': '#FFFFBE', 
    'Tropical Zona Equatorial, quente - média > 18° C em todos os meses, semi-árido 7 a 8 meses secos': '#FFFF00', 
    'Tropical Zona Equatorial, quente - média > 18° C em todos os meses, semi-árido 9 a 10 meses secos': '#F7941D', 
    'Tropical Zona Equatorial, quente - média > 18° C em todos os meses, semi-úmido 4 a 5 meses secos': '#F2EFF2', 
    'Tropical Zona Equatorial, quente - média > 18° C em todos os meses, super-úmido subseca': '#A378B9', 
    'Tropical Zona Equatorial, quente - média > 18° C em todos os meses, úmido 1 a 2 meses secos': '#D1AAD1', 
    'Tropical Zona Equatorial, quente - média > 18° C em todos os meses, úmido 3 meses secos': '#E6D4E6', 
    'Zona Contígua': '#ADD8E6', 
    'Zona Costeira': '#ADD8E6', 
    'Zona Exclusiva': '#ADD8E6'
}
normalized_color_map = {normalize_text(k): v for k, v in color_map.items()}


def get_color(desc):
    if pd.isna(desc): return "#808080"  # Cor para dados nulos
    return normalized_color_map.get(normalize_text(desc), "#E0E0E0")  # Cor padrão


def style_function_clima(feature):
    return {"fillColor": get_color(feature["properties"]["DESC_COMPL"]), "color": "none", "weight": 0, "fillOpacity": 0.7}

# --- FIM DA LÓGICA DE CLIMA ---


@lru_cache(maxsize=1)
def load_all_data():
    """Carrega e processa todos os arquivos de dados geoespaciais necessários."""
    logger.info("Iniciando carregamento de dados geoespaciais (cacheado)...")
    try:
        brasil_gdf = gpd.read_file(BASE_DIR / "data" / "FILE_GEOJSON" / "BR_UF_2024.geojson")
        matopiba_gdf = gpd.read_file(BASE_DIR / "data" / "FILE_GEOJSON" / "Matopiba_Perimetro.geojson")
        clima_gdf = gpd.read_file(BASE_DIR / "data" / "SHAPEFILE_CLIMA_BR" / "clima_5000.shp")
        cities_df = pd.read_csv(BASE_DIR / "data" / "FILE_CSV" / "CITIES_MATOPIBA_337.csv", sep=",")
        
        clima_gdf.set_crs(epsg=4674, inplace=True, allow_override=True)
        for gdf in [brasil_gdf, matopiba_gdf, clima_gdf]:
            gdf.to_crs(epsg=4326, inplace=True)
        
        logger.info("Dados geoespaciais carregados e processados com sucesso.")
        return brasil_gdf, matopiba_gdf, clima_gdf, cities_df
    except Exception as e:
        logger.error(f"Erro ao carregar dados geoespaciais: {e}")
        return None, None, None, None


def create_base_map_layers(t: Dict[str, str]):
    """Cria as camadas base (clima, estados e contorno do MATOPIBA)."""
    brasil_gdf, matopiba_gdf, clima_gdf, _ = load_all_data()
    
    if any(x is None for x in [brasil_gdf, matopiba_gdf, clima_gdf]):
        logger.error("Falha ao carregar GeoDataFrames para o mapa base.")
        return []

    layers = [
        dl.GeoJSON(
            data=clima_gdf.__geo_interface__,
            id="clima-brasil",
            style=style_function_clima,
            hoverStyle={"fillOpacity": 0.9},
            options={"name": t.get("climate_brasil", "Brazil Climate")}
        ),
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