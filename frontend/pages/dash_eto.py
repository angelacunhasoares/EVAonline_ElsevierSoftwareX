"""
EVAonline ETo Calculator Page
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def eto_calculator_dash(lang: str = "pt") -> dbc.Container:
    """
    Cria o layout da página ETo Calculator.
    
    Args:
        lang: Código do idioma (pt/en)
        
    Returns:
        dbc.Container: Layout da página
    """
    return dbc.Container([
        # Exibir localização selecionada
        html.Div(id='eto-location-info', className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.H1("ETo Calculator", className="text-center mb-4"),
                html.P(
                    "Página para cálculo da evapotranspiração de referência",
                    className="text-center lead"
                ),
                
                # Card com informações da localização
                dbc.Card([
                    dbc.CardHeader(
                        html.H5("📍 Localização Selecionada",
                                className="mb-0")
                    ),
                    dbc.CardBody(id='selected-location-display')
                ], className="mb-3"),
                
                # Card com formulário de período
                dbc.Card([
                    dbc.CardHeader(
                        html.H5("📅 Selecione o Período",
                                className="mb-0")
                    ),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Data Inicial:"),
                                dcc.DatePickerSingle(
                                    id='start-date-picker',
                                    display_format='DD/MM/YYYY',
                                    className="mb-2"
                                )
                            ], md=6),
                            dbc.Col([
                                html.Label("Data Final:"),
                                dcc.DatePickerSingle(
                                    id='end-date-picker',
                                    display_format='DD/MM/YYYY',
                                    className="mb-2"
                                )
                            ], md=6)
                        ]),
                        dbc.Button(
                            "Calcular ETo",
                            id="calculate-eto-btn",
                            color="primary",
                            className="mt-3 w-100"
                        )
                    ])
                ], className="mb-3"),
                
                # Área de resultados
                html.Div(id='eto-results', className="mt-3")
            ])
        ]),
        
        # Stores necessários para callbacks globais
        dcc.Store(id='favorites-store', data=[], storage_type='local')
    ], fluid=True)
