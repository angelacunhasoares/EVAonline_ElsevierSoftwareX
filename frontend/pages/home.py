"""
Página inicial do EVAonline com mapas interativos em abas.
"""
import sys
from pathlib import Path

import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash import dcc, html

# Adicionar backend ao path para importar map_results
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent.parent / "backend")
)
from core.map_results.map_results import create_matopiba_real_map


def create_world_map():
    """Cria um mapa mundial interativo com geolocalização."""
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
            html.Div(id='tab-content', children=[create_world_map()])
        ], className="container-fluid")
    ])
