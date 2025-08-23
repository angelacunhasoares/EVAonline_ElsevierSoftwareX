"""
Componente de rodapé para o aplicativo EVAOnline.
"""
from dash import html
import dash_bootstrap_components as dbc


def render_footer_bootswatch() -> html.Footer:
    """
    Cria um rodapé responsivo com informações de copyright.
    
    Returns:
        html.Footer: Componente do rodapé
    """
    copyright_text = html.P(
        "© 2025 EVAOnline Project",
        className="text-center text-muted"
    )
    
    return html.Footer(
        dbc.Container(
            dbc.Row(
                dbc.Col(copyright_text, width=12)
            ),
            className="mt-5 p-4 border-top"
        )
    )
