"""
Gerenciamento de rotas do frontend.
"""
from dash import html
import dash_bootstrap_components as dbc
from config.settings.app_settings import get_settings

settings = get_settings()

def create_navbar():
    """Cria a barra de navegação."""
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(
                dbc.NavLink("Calculadora ETo", href=settings.DASH_ROUTES["eto_calculator"])
            ),
            dbc.NavItem(
                dbc.NavLink("Sobre", href=settings.DASH_ROUTES["about"])
            ),
        ],
        brand="EVAonline",
        brand_href=settings.DASH_ROUTES["home"],
        color="primary",
        dark=True,
        className="mb-4",
    )

def create_home_layout():
    """Layout da página inicial."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("EVAonline", className="text-center mb-4"),
                html.P(
                    "Ferramenta online para estimativa da evapotranspiração de referência (ETo)",
                    className="text-center lead"
                ),
                dbc.Button(
                    "Iniciar Cálculo",
                    href=settings.DASH_ROUTES["eto_calculator"],
                    color="primary",
                    className="mx-auto d-block mt-4"
                )
            ])
        ])
    ])

def create_about_layout():
    """Layout da página Sobre."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Sobre o EVAonline", className="mb-4"),
                html.P("Informações sobre o projeto..."),
                # Adicione mais conteúdo aqui
            ])
        ])
    ])

def create_eto_calculator_layout():
    """Layout da calculadora ETo."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Calculadora ETo", className="mb-4"),
                # Seu formulário e componentes da calculadora aqui
            ])
        ])
    ])

def render_page_content(pathname):
    """
    Renderiza o conteúdo com base na URL atual.
    """
    if pathname == settings.DASH_ROUTES["home"]:
        return create_home_layout()
    elif pathname == settings.DASH_ROUTES["eto_calculator"]:
        return create_eto_calculator_layout()
    elif pathname == settings.DASH_ROUTES["about"]:
        return create_about_layout()
    
    # Página 404
    return dbc.Container([
        html.H1("404: Página não encontrada", className="text-danger"),
        html.P(f"A página {pathname} não existe."),
        dbc.Button("Voltar para Home", href=settings.DASH_ROUTES["home"])
    ])
