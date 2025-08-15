import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import requests
from loguru import logger
from prometheus_client import Counter, generate_latest
from flask import Response
import json
from redis import Redis
from components.navbar import render_navbar
from components.footer import render_footer
from utils.language_manager import init_language
from utils.get_translations import get_translations  # Atualizado
from src.map_generator import create_interactive_map, map_all_cities, map_piracicaba_city
from utils.logging import configure_logging

configure_logging()
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, "/assets/fontawesome.css", "/assets/styles.css"],
    suppress_callback_exceptions=True
)

# Métrica do Prometheus
REQUESTS_DASH = Counter('evaonline_dash_requests_total', 'Total Dash Requests')

@app.server.route("/metrics")
def metrics():
    REQUESTS_DASH.inc()
    return Response(generate_latest(), mimetype="text/plain")

# Inicializar Redis
redis_client = Redis.from_url("redis://redis:6379/0")

# Cachear traduções
def get_translations(lang: str = "pt"):
    cache_key = f"translations:{lang}"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            logger.info(f"Traduções carregadas do Redis para o idioma {lang}")
            return json.loads(cached)
        t = get_translations(lang)
        redis_client.setex(cache_key, 3600, json.dumps(t))
        logger.info(f"Traduções salvas no Redis para o idioma {lang}")
        return t
    except Exception as e:
        logger.error(f"Erro ao acessar traduções no Redis: {str(e)}")
        return get_translations(lang)  # Fallback para traduções locais

# Inicializar traduções
t = init_language(app)

app.layout = dbc.Container([
    render_navbar(t),
    dcc.Location(id="url"),
    html.Div(id="page-content"),
    dcc.Store(id="selected-map", data=t["map_options"][0]),
    dcc.Store(id="selected-coordinates"),
    render_footer()
])

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("language-store", "data")
)
def display_page(pathname, lang):
    t = get_translations(lang)
    if pathname == "/about":
        from pages.about import layout
        return layout
    if pathname == "/eto":
        from pages.eto_dashboard import create_layout
        return create_layout(lang=lang)
    return html.Div([
        html.H5(t["choose_map"], style={"color": "#012D5A", "margin-bottom": "3px"}),
        dcc.RadioItems(
            id="map-radio",
            options=[{"label": opt, "value": opt} for opt in t["map_options"]],
            value=t["map_options"][0],
            labelStyle={"display": "block"}
        ),
        html.Div(id="map-container"),
        html.P(id="map-desc"),
        html.Div(id="legend"),
        html.P(id="coords-output"),
        dbc.Button(f"🌦️ {t['calculate_eto']}", id="calculate-eto-button", color="primary", disabled=True),
        html.Div(id="alert-container")
    ])

@app.callback(
    Output("selected-map", "data"),
    Input("map-radio", "value")
)
def update_map_selection(selected_map):
    t = get_translations()  # Usa idioma padrão
    if selected_map not in t["map_options"]:
        logger.warning(f"Mapa selecionado inválido: {selected_map}")
        return t["map_options"][0]
    return selected_map

@app.callback(
    Output("map-container", "children"),
    Output("map-desc", "children"),
    Output("legend", "children"),
    Input("selected-map", "data"),
    State("language-store", "data")
)
def render_map(selected_map, lang):
    t = get_translations(lang)
    logger.info(f"Renderizando mapa: {selected_map}")
    if not selected_map:
        return html.P(t["no_map_selected"], className="text-danger text-center"), "", ""
    
    if selected_map == t["map_options"][0]:
        map_obj = map_all_cities()
        map_desc = t["map_desc_interactive"]
        legend_html = f"""
        <div class="map-legend">
            <b>{t['legend']}</b><br>
            <i class="fa fa-map-marker" style="color: purple; font-size: 16px;"></i> {t['legend_map1_cities']} <strong>{t['legend_map1_zoom']}</strong><br>
            <span style="color: red; font-size: 16px;">━</span> {t['perimeter']}<br>
            <b>{t['source']}:</b> {t['map_source_all_cities']}
        </div>
        """
        center = [-10, -55]
        zoom = 4
    elif selected_map == t["map_options"][1]:
        map_obj = map_piracicaba_city()
        map_desc = t["map2_desc"]
        legend_html = f"""
        <div class="map-legend">
            <b>{t['legend']}</b><br>
            <i class="fa fa-map-marker" style="color: green; font-size: 16px;"></i> {t['legend_map2_city']}<br>
            <span style="color: red; font-size: 16px;">━</span> {t['legend_map2_perimeter']}<br>
            <strong>{t['source']}:</strong> IBGE (Perímetro)
        </div>
        """
        center = [-22.725, -47.649]
        zoom = 10
    else:
        map_obj = create_interactive_map()
        map_desc = t["map_desc_interactive"]
        legend_html = f"""
        <div class="map-legend" style="padding: 10px; background-color: white; border: 2px solid black; border-radius: 5px;">
            <b>{t['legend']}</b><br>
            <i class="fa fa-globe" style="color: blue; font-size: 16px;"></i> {t['legend_map4_global']}<br>
        </div>
        """
        center = [0, 0]
        zoom = 1

    return dl.Map(
        [dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"), map_obj],
        id="map",
        center=center,
        zoom=zoom,
        style={"width": "100%", "height": "50vh"}
    ), map_desc, html.Div(legend_html, className="map-legend")

@app.callback(
    Output("coords-output", "children"),
    Output("selected-coordinates", "data"),
    Input("map", "click_lat_lng"),
    State("selected-map", "data"),
    State("language-store", "data")
)
def capture_coordinates(click_lat_lng, selected_map, lang):
    t = get_translations(lang)
    if selected_map == t["map_options"][2] and click_lat_lng:
        lat, lng = click_lat_lng
        try:
            response = requests.get(f"http://api:8000/get_elevation?lat={lat}&lng={lng}")
            data = response.json()
            if "error" in data:
                logger.error(f"Erro ao obter elevação: {data['error']}")
                return f"{t['error_elevation']}: {data['error']}", None
            elev = data.get("elevation", 100)
            warnings = data.get("warnings", [])
            for w in warnings:
                logger.warning(w)
            logger.info(f"Coordenadas capturadas: lat={lat}, lng={lng}, elev={elev}")
            return f"{t['coords_captured']}: Latitude: {lat:.6f}, Longitude: {lng:.6f}, {t['elevation']}: {elev}m", {"lat": lat, "lng": lng, "elev": elev}
        except Exception as e:
            logger.error(f"Erro na requisição de elevação: {str(e)}")
            return f"{t['error_elevation']}: {str(e)}", None
    return "", None

@app.callback(
    Output("url", "pathname"),
    Output("alert-container", "children"),
    Input("calculate-eto-button", "n_clicks"),
    State("selected-coordinates", "data")
)
def navigate_to_eto(n_clicks, coords):
    t = get_translations()  # Usa idioma padrão
    if n_clicks and coords:
        return "/eto", None
    elif n_clicks:
        return dash.no_update, dbc.Alert(t["no_coords_selected"], color="danger")
    return dash.no_update, None

@app.callback(
    Output("calculate-eto-button", "disabled"),
    Input("selected-coordinates", "data")
)
def toggle_button(coords):
    return not bool(coords)

if __name__ == "__main__":
    app.run_server(debug=True, port=8050)