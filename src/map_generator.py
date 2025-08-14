import logging
from pathlib import Path
import dash_leaflet as dl
import geopandas as gpd
import pandas as pd
import re
from functools import lru_cache
from utils.get_translations import get_translations
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração de diretório base
BASE_DIR = Path(os.getenv("BASE_DIR", Path(__file__).parent.parent))


def style_function_brasil(feature):
    return {"fillOpacity": 0, "color": "#505050", "weight": 1}


def style_function_matopiba(feature):
    return {"color": "#FF0000", "weight": 2.5, "fillOpacity": 0}


@lru_cache(maxsize=1)
def load_all_data():
    """Carrega e processa todos os arquivos de dados necessários."""
    logger.info("Iniciando carregamento de todos os dados...")
    
    try:
        brasil_gdf = gpd.read_file(BASE_DIR / "data" / "FILE_GEOJSON" / "BR_UF_2024.geojson")
        logger.info("BR_UF_2024.geojson carregado com sucesso")
        matopiba_gdf = gpd.read_file(BASE_DIR / "data" / "FILE_GEOJSON" / "Matopiba_Perimetro.geojson")
        logger.info("Matopiba_Perimetro.geojson carregado com sucesso")
        clima_gdf = gpd.read_file(BASE_DIR / "data" / "SHAPEFILE_CLIMA_BR" / "clima_5000.shp")
        logger.info("clima_5000.shp carregado com sucesso")

        # Correção e alinhamento de CRS
        clima_gdf.set_crs(epsg=4674, inplace=True, allow_override=True)
        for gdf in [brasil_gdf, matopiba_gdf, clima_gdf]:
            gdf.to_crs(epsg=4326, inplace=True)

        logger.info("Todos os dados foram carregados e processados com sucesso.")
        return brasil_gdf, matopiba_gdf, clima_gdf

    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
        return None, None, None


def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower().replace("º", " ").replace("°", " ")
    text = text.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c")
    text = text.replace("â", "a").replace("ê", "e")
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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
    if pd.isna(desc):
        return "#808080"
    return normalized_color_map.get(normalize_text(desc), "#E0E0E0")


def style_function_clima(feature):
    return {"fillColor": get_color(feature["properties"]["DESC_COMPL"]), "color": "none", "weight": 0, "fillOpacity": 0.7}


def create_climate_base_map():
    """Cria uma camada base com clima, estados e MATOPIBA."""
    logger.info("Criando mapa base com clima...")
    brasil_gdf, matopiba_gdf, clima_gdf = load_all_data()
    
    if any(x is None for x in [brasil_gdf, matopiba_gdf, clima_gdf]):
        logger.error("Falha ao carregar GeoDataFrames.")
        return dl.LayerGroup()

    t = get_translations()
    layers = []
    if clima_gdf is not None:
        layers.append(
            dl.GeoJSON(
                data=clima_gdf.__geo_interface__,
                id="clima-brasil",
                style=style_function_clima,
                hoverStyle={"fillOpacity": 0.9},
                options={"name": t["climate_brasil"]}
            )
        )
    if brasil_gdf is not None:
        layers.append(
            dl.GeoJSON(
                data=brasil_gdf.__geo_interface__,
                id="limites-estaduais",
                style=style_function_brasil,
                options={"name": t["state_borders"], "show": False}
            )
        )
    if matopiba_gdf is not None:
        layers.append(
            dl.GeoJSON(
                data=matopiba_gdf.__geo_interface__,
                id="contorno-matopiba",
                style=style_function_matopiba,
                options={"name": t["matopiba_contour"]}
            )
        )
    return dl.LayerGroup(layers, id="base-layers")


def map_all_cities():
    logger.info("Gerando mapa de todas as cidades do MATOPIBA")
    t = get_translations()
    base_layers = create_climate_base_map()
    cities_df = pd.read_csv(BASE_DIR / "data" / "FILE_CSV" / "CITIES_MATOPIBA_337.csv", sep=",")

    markers = [
        dl.Marker(
            position=[row["LATITUDE"], row["LONGITUDE"]],
            children=[
                dl.Tooltip(row.get("CITY", "Desconhecido")),
                dl.Popup(f"{t['map_popup_city']}: {row.get('CITY', 'Desconhecido')} ({row.get('UF', 'N/A')})<br>{t['map_popup_coordinates']}: ({row['LATITUDE']:.6f}, {row['LONGITUDE']:.6f})")
            ],
            icon={"icon": "fa-map-marker", "iconColor": "purple"}
        ) for _, row in cities_df.iterrows() if not (pd.isna(row["LATITUDE"]) or pd.isna(row["LONGITUDE"]))
    ]
    return dl.LayerGroup([base_layers, dl.LayerGroup(markers, id="cities-cluster")], id="map-all-cities")


def map_piracicaba_city():
    logger.info("Gerando mapa da cidade de Piracicaba")
    t = get_translations()
    base_layers = create_climate_base_map()
    cities_df = pd.read_csv(BASE_DIR / "data" / "FILE_CSV" / "CITY_PIRACICABA_SP.csv", sep=",", encoding="utf-8")

    markers = [
        dl.Marker(
            position=[row["LATITUDE"], row["LONGITUDE"]],
            children=[
                dl.Tooltip("Piracicaba"),
                dl.Popup(f"{t['map_popup_city']}: {row.get('CITY', 'Piracicaba')} ({row.get('UF', 'SP')})<br>{t['map_popup_coordinates']}: ({row['LATITUDE']:.6f}, {row['LONGITUDE']:.6f})<br>{t['map_popup_note']}: Developed EVAonline here!")
            ],
            icon={"icon": "fa-info-sign", "iconColor": "green"}
        ) for _, row in cities_df.iterrows() if not (pd.isna(row["LATITUDE"]) or pd.isna(row["LONGITUDE"]))
    ]
    return dl.LayerGroup([base_layers, dl.LayerGroup(markers)], id="map-piracicaba")


def create_interactive_map():
    logger.info("Gerando mapa global interativo")
    t = get_translations()
    return dl.LayerGroup([
        dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"),
        dl.Marker(
            position=[0, 0],
            children=[dl.Tooltip(t["click_to_select"])],
            icon={"icon": "fa-globe", "iconColor": "blue"}
        )
    ], id="interactive-layer")