"""
Página inicial do EVAonline com mapas interativos em abas.
"""
import sys
from pathlib import Path

import dash_bootstrap_components as dbc
from dash import dcc, html

# Adicionar backend ao path para importar map_results
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent.parent / "backend")
)
from core.map_results.map_results import create_world_real_map
from core.map_results.matopiba_forecasts import \
    create_matopiba_forecast_section


# Layout da página inicial com mapas em abas (agora com renderização dinâmica)
def home_layout() -> html.Div:
    """
    Cria o layout da página inicial com mapas interativos em abas.

    Returns:
        html.Div: Layout da página inicial
    """
    return html.Div([
        # Stores para persistência de dados (locais da página home)
        dcc.Store(id='markers-store', data=[]),
        dcc.Store(id='favorites-store', data=[], storage_type='local'),
        
        dbc.Container([
            # Header com título e abas (extra compacto)
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-map-marked-alt me-2",
                              style={"fontSize": "13px", "color": "#2d5016"}),
                        html.Strong("Selecione o Mapa", 
                                   style={"fontSize": "13px", "color": "#2d5016"})
                    ], className="mb-2"),
                    dbc.Tabs(
                        [
                            dbc.Tab(
                                label="🌍 Mapa Mundial",
                                tab_id="world-tab",
                                label_style={"fontSize": "14px",
                                            "fontWeight": "500",
                                            "padding": "6px 12px"}
                            ),
                            dbc.Tab(
                                label="🌾 MATOPIBA, Brasil",
                                tab_id="matopiba-tab",
                                label_style={"fontSize": "14px",
                                            "fontWeight": "500",
                                            "padding": "6px 12px"}
                            ),
                        ],
                        id="map-tabs",
                        active_tab="world-tab",
                    )
                ], className="py-2 px-3")
            ], className="mb-1 shadow-sm"),

            # Conteúdo dinâmico da aba (será preenchido pelo callback)
            html.Div(id='tab-content', children=[create_world_real_map()])
        ], className="container-fluid")
    ])
