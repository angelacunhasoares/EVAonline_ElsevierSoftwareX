"""
EVAonline About Page
"""

from dash import html
import dash_bootstrap_components as dbc


def layout(lang: str = "pt") -> dbc.Container:
    """
    Cria o layout da página About.
    
    Args:
        lang: Código do idioma (pt/en)
        
    Returns:
        dbc.Container: Layout da página
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("About EVAonline", className="text-center mb-4"),
                html.P(
                    "Sistema para cálculo de evapotranspiração de referência",
                    className="text-center lead"
                ),
                html.P(
                    "Este é um sistema desenvolvido para auxiliar no cálculo "
                    "da evapotranspiração de referência (ETo) utilizando "
                    "dados meteorológicos.",
                    className="text-center"
                )
            ])
        ])
    ], fluid=True)