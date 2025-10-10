"""
EVAonline ETo Calculator Page
"""

from datetime import datetime, timedelta

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
    # Configurações de período (validação)
    today = datetime.now()
    min_date = today - timedelta(days=365)  # 1 ano atrás
    max_date = today + timedelta(days=1)    # Amanhã
    
    return dbc.Container([
        # Exibir localização selecionada
        html.Div(id='eto-location-info', className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.H1("ETo Calculator", className="text-center mb-4"),
                html.P(
                    "Cálculo da evapotranspiração de referência com "
                    "múltiplas fontes de dados climáticos",
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
                
                # Card com seletor de fontes de dados (NOVO)
                html.Div(id='climate-sources-card'),
                
                # Card com formulário de período
                dbc.Card([
                    dbc.CardHeader(
                        html.H5("📅 Selecione o Período",
                                className="mb-0")
                    ),
                    dbc.CardBody([
                        # Informação sobre limites de período
                        dbc.Alert([
                            html.I(className="bi bi-info-circle me-2"),
                            html.Strong("Período permitido: "),
                            f"Mínimo 7 dias, máximo 15 dias. "
                            f"Dados disponíveis de {min_date.strftime('%d/%m/%Y')} "
                            f"até {max_date.strftime('%d/%m/%Y')}."
                        ], color="info", className="mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                html.Label("Data Inicial:"),
                                dcc.DatePickerSingle(
                                    id='start-date-picker',
                                    display_format='DD/MM/YYYY',
                                    min_date_allowed=min_date,
                                    max_date_allowed=max_date,
                                    initial_visible_month=today,
                                    date=today - timedelta(days=7),
                                    className="mb-2"
                                )
                            ], md=6),
                            dbc.Col([
                                html.Label("Data Final:"),
                                dcc.DatePickerSingle(
                                    id='end-date-picker',
                                    display_format='DD/MM/YYYY',
                                    min_date_allowed=min_date,
                                    max_date_allowed=max_date,
                                    initial_visible_month=today,
                                    date=today,
                                    className="mb-2"
                                )
                            ], md=6)
                        ]),
                        
                        # Validação de período
                        html.Div(id='period-validation', className="mt-2"),
                        
                        dbc.Button(
                            "Calcular ETo",
                            id="calculate-eto-btn",
                            color="primary",
                            className="mt-3 w-100",
                            disabled=False
                        )
                    ])
                ], className="mb-3"),
                
                # Área de resultados
                html.Div(id='eto-results', className="mt-3")
            ])
        ]),
        
        # Stores necessários para callbacks globais
        dcc.Store(id='favorites-store', data=[], storage_type='local'),
        dcc.Store(id='selected-location-store', storage_type='session'),
        dcc.Store(id='available-sources-store', storage_type='session'),
        dcc.Store(id='selected-sources-store', storage_type='session')
    ], fluid=True)
