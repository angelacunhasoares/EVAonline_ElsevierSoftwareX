"""
EVAonline ETo Calculator Page
"""

from dash import html
import dash_bootstrap_components as dbc


def create_layout(lang: str = "pt") -> dbc.Container:
    """
    Cria o layout da página ETo Calculator.
    
    Args:
        lang: Código do idioma (pt/en)
        
    Returns:
        dbc.Container: Layout da página
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("ETo Calculator", className="text-center mb-4"),
                html.P(
                    "Página para cálculo da evapotranspiração de referência",
                    className="text-center lead"
                )
            ])
        ])
    ], fluid=True)