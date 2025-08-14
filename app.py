import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import requests
from loguru import logger
from components.navbar import render_navbar
from components.footer import render_footer
from utils.language_manager import init_language
from utils.get_translations import get_translations
from src.map_generator import create_interactive_map, map_all_cities, map_piracicaba_city
from utils.logging import configure_logging

configure_logging()
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Inicializar traduções
t = init_language(app)

app.layout = dbc.Container([
    render_navbar(t),
    dcc.Location(id="url"),
    html.Div(id="page-content"),
    dcc.Store(id="selected-map", data=t["map_options"][0]),  # Mapa padrão: MATOPIBA
    dcc.Store(id="selected-coordinates"),
    render_footer()
])


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("language-store", "data")
)
def display_page(pathname, lang):
    t = get_translations()
    if pathname == "/about":
        from pages.about import layout
        return layout
    if pathname == "/eto":
        from pages.eto_dashboard import layout
        return layout
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
        dbc.Button(f"🌦️ {t['calculate_eto']}", id="calculate-eto-button", color="primary"),
    ])


@app.callback(
    Output("selected-map", "data"),
    Input("map-radio", "value")
)
def update_map_selection(selected_map):
    return selected_map


@app.callback(
    Output("map-container", "children"),
    Output("map-desc", "children"),
    Output("legend", "children"),
    Input("selected-map", "data"),
    State("language-store", "data")
)
def render_map(selected_map, lang):
    t = get_translations()
    if not selected_map:
        return html.P(t["no_map_selected"], style={"color": "#6c757d", "text-align": "center"}), "", ""
    
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
        center = [-22.725, -47.649]  # Centralizar em Piracicaba
        zoom = 10
    else:  # Mapa interativo global
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
    t = get_translations()
    if selected_map == t["map_options"][2] and click_lat_lng:
        lat, lng = click_lat_lng
        response = requests.get(f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lng}")
        elev = response.json().get("elevation", 100)
        logger.info(f"Coordenadas capturadas: lat={lat}, lng={lng}, elev={elev}")
        return f"{t['coords_captured']}: Latitude: {lat:.6f}, Longitude: {lng:.6f}, {t['elevation']}: {elev}m", {"lat": lat, "lng": lng, "elev": elev}
    return "", None


@app.callback(
    Output("url", "pathname"),
    Input("calculate-eto-button", "n_clicks"),
    State("selected-coordinates", "data")
)
def navigate_to_eto(n_clicks, coords):
    if n_clicks and coords:
        return "/eto"
    return dash.no_update


if __name__ == "__main__":
    app.run_server(debug=True, port=8050)