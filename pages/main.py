"""
# frontend/
# Este módulo implementa a página principal do aplicativo EVAonline, com:
- Seleção interativa de mapas e visualização com interface em abas
- Inglês como idioma padrão com opção de mudar para Português
- Três mapas diferentes: Mapa Mundial, Mapa das Cidades MATOPIBA e Mapa da Cidade de Piracicaba
- Navegação para outras seções do aplicativo.

A página serve como ponto de entrada para os usuários selecionarem locais e iniciarem
cálculos de ETo (evapotranspiração de referência).
"""

from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from prometheus_flask_exporter import PrometheusMetrics
from dash_extensions import WebSocket
from src import map_generator (create_interactive_map, map_all_cities, map_piracicaba_city)  # Importa as funções de mapas

# Configuração do Dash
app = Dash(__name__, external_stylesheets=[{"href": "assets/styles.css", "rel": "stylesheet"}])
app.title = "EVAonline"
metrics = PrometheusMetrics(app.server)

# Layout da página inicial com tabs DBC e GIF
app.layout = html.Div([
    # Cabeçalho com GIF
    html.Header(
        style={
            "backgroundImage": "url('https://media.giphy.com/media/3o7TKTDnHRnS1uXHMk/giphy.gif')",  # Exemplo de GIF (substitua por seu GIF)
            "backgroundSize": "cover",
            "backgroundPosition": "center",
            "height": "200px",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "color": "white",
            "textShadow": "2px 2px 4px rgba(0, 0, 0, 0.7)"
        },
        children=[
            html.Div([
                html.H1("MATOPIBADash", style={"margin": "0"}),
                html.H4("Online Tool for MATOPIBA Climate and City Analysis", style={"margin": "0"})
            ])
        ]
    ),
    # Menu de Navegação com Tabs DBC
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Mapa Global", href="#", id="tab-global")),
            dbc.NavItem(dbc.NavLink("Mapa ETo MATOPIBA", href="#", id="tab-matopiba")),
            dbc.NavItem(dbc.NavLink("Piracicaba, SP Brasil", href="#", id="tab-piracicaba")),
            dbc.NavItem(dbc.Button("ENGLISH", id="language-toggle", color="primary", outline=True, className="ms-auto"))
        ],
        brand="",
        color="light",
        dark=False,
        expand="lg"
    ),
    # Corpo Principal com Tabs
    dbc.Tabs(
        id="tabs",
        active_tab="tab-global",
        children=[
            dbc.Tab(label="Mapa Global", tab_id="tab-global"),
            dbc.Tab(label="Mapa ETo MATOPIBA", tab_id="tab-matopiba"),
            dbc.Tab(label="Piracicaba, SP Brasil", tab_id="tab-piracicaba")
        ]
    ),
    html.Div(id="tab-content", className="p-4"),
    # Instruções
    html.P("Interactive Map: Click to capture coordinates and analyze climate data", className="text-center", style={"marginTop": "10px"}),
    # Rodapé
    html.Footer(
        className="bg-light text-center py-3 mt-4",
        children=[
            html.P("© 2025 MATOPIBADash Project | Powered by Leaflet, OpenStreetMap, and CARTO")
        ]
    ),
    # Componente WebSocket
    WebSocket(id="ws", url="ws://fastapi:8000/ws_geo_data"),  # Ajustado para evitar conflito
    # Armazenar estado do mapa
    dcc.Store(id="map-state", data={"map_type": "global"})
])

# Callback para atualizar o conteúdo dos tabs
@app.callback(
    [dash.dependencies.Output("tab-content", "children"),
     dash.dependencies.Output("map-state", "data")],
    [dash.dependencies.Input("tabs", "active_tab"),
     dash.dependencies.Input("ws", "message")]
)
def update_tab_content(active_tab, message):
    if active_tab == "tab-matopiba":
        map_type = "matopiba"
        center = [-10, -55]
        zoom = 4
    elif active_tab == "tab-piracicaba":
        map_type = "piracicaba"
        center = [-22.725, -47.649]
        zoom = 10
    else:  # tab-global
        map_type = "global"
        center = [0, 0]
        zoom = 2
    
    heatmap_points = [[point["lat"], point["lon"], point.get("intensity", 1)] for point in (message.get("data", []) if message else [])]
    map_obj, _, _, map_desc, legend_html = maps.map_all_cities(t, map_type=map_type, heatmap_points=heatmap_points)
    
    return [
        html.Div([
            dl.Map(
                id="map",
                children=[
                    dl.TileLayer(url="http://nginx:80/tiles/{z}/{x}/{y}.png"),
                    dl.LayerGroup(id="map-layers", children=[map_obj])
                ],
                center=center,
                zoom=zoom,
                style={'width': '100%', 'height': '600px'}
            ),
            html.Div(className="col-md-3", children=[
                html.Div(legend_html, className="card", style={"padding": "15px"}, dangerously_set_inner_html="")
            ], style={"position": "absolute", "right": "10px", "top": "250px", "width": "250px"})
        ]),
        {"map_type": map_type}
    ], prevent_initial_call=True

# Callback para alternar idioma (simplificado)
@app.callback(
    dash.dependencies.Output("language-toggle", "children"),
    [dash.dependencies.Input("language-toggle", "n_clicks")]
)
def toggle_language(n_clicks):
    if n_clicks and n_clicks % 2 == 1:
        return "PORTUGUÊS"
    return "ENGLISH"

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)