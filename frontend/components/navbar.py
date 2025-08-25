"""
Componente de barra de navegação para o aplicativo EVAOnline.
"""
import dash_bootstrap_components as dbc
from dash import html


def render_navbar_bootswatch(translations: dict,
                             current_lang: str = 'en') -> dbc.NavbarSimple:
    """
    Cria uma barra de navegação responsiva com menu de idiomas.
    
    Args:
        translations (dict): Dicionário com as traduções
        current_lang (str): Código do idioma atual (en/pt)
    
    Returns:
        dbc.NavbarSimple: Componente da barra de navegação
    """
    nav_items = [
        dbc.NavItem(dbc.NavLink(translations["home"], href="/")),
        dbc.NavItem(dbc.NavLink("ETo Dashboard", href="/eto")),
        dbc.NavItem(dbc.NavLink(translations["about"], href="/about")),
    ]
    
    language_menu = dbc.DropdownMenu(
        children=[
            dbc.DropdownMenuItem(
                "English",
                id={'type': 'lang-select', 'lang': 'en'}
            ),
            dbc.DropdownMenuItem(
                "Português",
                id={'type': 'lang-select', 'lang': 'pt'}
            ),
        ],
        nav=True,
        in_navbar=True,
        label=current_lang.upper(),
    )
    
    # Adicionar o menu de idiomas diretamente na lista de children
    return dbc.NavbarSimple(
        children=nav_items + [language_menu],
        brand="EVAOnline",
        brand_href="/",
        color="primary",
        dark=True,
        className="mb-4",
    )
