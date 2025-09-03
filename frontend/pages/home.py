"""
Página inicial do EVAonline com mapas interativos em abas.
"""
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import numpy as np
import pandas as pd
import plotly.express as px
from dash import dcc, html


def create_world_map():
    """Cria um mapa mundial interativo com geolocalização."""
    # Layout do mapa com Dash Leaflet
    map_layout = html.Div([
        # Componente de geolocalização
        dcc.Geolocation(
            id='geolocation',
            update_now=False,
            high_accuracy=True,
            maximum_age=0,
            timeout=10000,
            show_alert=True
        ),

        # Container para informações de localização
        html.Div([
            html.H5("Sua Localização:", className="mt-3"),
            html.Div(id='location-info', className="alert alert-info",
                     children="Clique em 'Obter Localização' para ver "
                              "sua posição."),
            html.Button('Obter Localização', id='get-location-btn',
                        className="btn btn-primary mt-2"),
        ], className="mb-3"),

        # Container para informações de clique no mapa
        html.Div([
            html.H5("Ponto Selecionado no Mapa:", className="mt-3"),
            html.Div(id='click-info', className="alert alert-success",
                     children="Clique em qualquer ponto do mapa para ver "
                              "as coordenadas."),
        ], className="mb-3"),

        # Mapa Leaflet
        dl.Map([
            dl.TileLayer(),
            # Marcador para localização do usuário (inicialmente oculto)
            dl.Marker(
                id='user-location-marker',
                position=[0, 0],
                children=[
                    dl.Tooltip("Sua Localização"),
                    dl.Popup("Esta é sua localização atual!")
                ]
            )
        ],
            center=[20, 0],
            zoom=2,
            style={
                'width': '100%',
                'height': '500px',
                'cursor': 'pointer',
                'position': 'relative'
            },
            id="map",
            dragging=True,
            scrollWheelZoom=True,
            doubleClickZoom=True,
            boxZoom=True,
            keyboard=True),

        # Legenda
        html.Div([
            html.H6("Legenda:", className="mt-3"),
            html.Ul([
                html.Li("📍 Sua localização (aparece após permitir "
                        "geolocalização)"),
                html.Li("👆 Clique no mapa para ver coordenadas")
            ])
        ], className="mt-3")
    ])

    return map_layout


def create_matopiba_map():
    """Cria um mapa da região MATOPIBA."""
    # Dados simulados para a região MATOPIBA
    np.random.seed(42)
    lats = np.random.uniform(-12, -2, 50)
    lons = np.random.uniform(-50, -40, 50)
    eto_values = np.random.uniform(3.0, 6.0, 50)

    df = pd.DataFrame({
        'latitude': lats,
        'longitude': lons,
        'eto': eto_values
    })

    fig = px.scatter_mapbox(df,
                            lat='latitude',
                            lon='longitude',
                            size='eto',
                            color='eto',
                            zoom=5,
                            center={'lat': -7, 'lon': -45},
                            title='Mapa de ETo: Horários de atualizações',
                            color_continuous_scale='RdYlBu_r')

    fig.update_layout(
        mapbox_style='open-street-map',
        margin=dict(l=0, r=0, t=50, b=0)
    )

    return dcc.Graph(figure=fig)


def create_piracicaba_map():
    """Cria um mapa detalhado de Piracicaba."""
    # Dados simulados para Piracicaba
    np.random.seed(123)
    lats = np.random.uniform(-22.75, -22.65, 30)
    lons = np.random.uniform(-47.65, -47.55, 30)
    eto_values = np.random.uniform(2.5, 5.5, 30)

    df = pd.DataFrame({
        'latitude': lats,
        'longitude': lons,
        'eto': eto_values
    })

    fig = px.scatter_mapbox(df,
                            lat='latitude',
                            lon='longitude',
                            size='eto',
                            color='eto',
                            zoom=12,
                            center={'lat': -22.7, 'lon': -47.6},
                            title='Piracicaba, SP - Valores de ETo',
                            color_continuous_scale='YlOrRd')

    fig.update_layout(
        mapbox_style='open-street-map',
        margin=dict(l=0, r=0, t=50, b=0)
    )

    return dcc.Graph(figure=fig)


# Layout da página inicial com mapas em abas
def layout() -> dbc.Container:
    """
    Cria o layout da página inicial com mapas interativos em abas.
    
    Returns:
        dbc.Container: Layout da página inicial
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("EVAonline - Sistema de Evapotranspiração",
                        className="text-center mb-4"),
                html.P(
                    "Selecione um mapa para visualizar os valores de "
                    "evapotranspiração de referência (ETo) em diferentes regiões.",
                    className="text-center lead mb-4"
                )
            ], width=12)
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Tabs([
                    dbc.Tab(
                        label="🌍 Mapa Mundial",
                        tab_id="world",
                        children=[
                            html.Div([create_world_map()], className="p-3")
                        ]
                    ),
                    dbc.Tab(
                        label="🌾 MATOPIBA, Brasil",
                        tab_id="matopiba",
                        children=[
                            html.Div([
                                html.P(
                                    "Região MATOPIBA (Maranhão, Tocantins, Piauí, "
                                    "Bahia). Dados atualizados 3x por dia.",
                                    className="mb-3"
                                ),
                                create_matopiba_map()
                            ], className="p-3")
                        ]
                    ),
                    dbc.Tab(
                        label="🏙️ Piracicaba, SP, Brasil",
                        tab_id="piracicaba",
                        children=[
                            html.Div([
                                html.P(
                                    "Cidade de Piracicaba, SP - Brasil. "
                                    "Visualização detalhada dos valores de ETo.",
                                    className="mb-3"
                                ),
                                create_piracicaba_map()
                            ], className="p-3")
                        ]
                    )
                ], active_tab="world")
            ], width=12)
        ]),

        dbc.Row([
            dbc.Col([
                html.Hr(),
                html.P(
                    "💡 Dica: Use as abas acima para alternar entre diferentes "
                    "visualizações de mapas e explore os dados de ETo.",
                    className="text-center text-muted"
                )
            ], width=12)
        ])
    ], fluid=True)
