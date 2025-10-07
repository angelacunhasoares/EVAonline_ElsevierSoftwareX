"""
Componente de barra de navegação para o aplicativo EVAOnline.
"""
import dash_bootstrap_components as dbc
from dash import html


def render_navbar(settings, current_lang: str = 'en') -> dbc.Navbar:
    """
    Cria uma barra de navegação responsiva e moderna.
    
    Args:
        settings: Configurações da aplicação
        current_lang (str): Código do idioma atual (en/pt)
    
    Returns:
        dbc.Navbar: Componente da barra de navegação
    """
    
    # Links de navegação com cor branca
    nav_items = dbc.Row([
        dbc.Col(
            dbc.NavLink(
                [
                    html.I(className="fas fa-calculator me-2"),
                    "Calculate ET",
                    html.Sub("0", className="ms-1")
                ],
                href=settings.DASH_ROUTES["eto_calculator"],
                className="nav-link-custom px-3",
                style={"color": "white"}
            ),
            width="auto",
            className="me-2"
        ),
        dbc.Col(
            dbc.NavLink(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "About"
                ],
                href=settings.DASH_ROUTES["about"],
                className="nav-link-custom px-3",
                style={"color": "white"}
            ),
            width="auto",
            className="me-2"
        ),
        dbc.Col(
            dbc.NavLink(
                [
                    html.I(className="fas fa-book me-2"),
                    "Docs"
                ],
                href=settings.DASH_ROUTES["documentation"],
                className="nav-link-custom px-3",
                style={"color": "white"}
            ),
            width="auto",
            className="me-3"
        ),
        dbc.Col(
            dbc.Button(
                [
                    html.I(className="fas fa-globe me-2"),
                    "English" if current_lang == 'en' else "Português"
                ],
                id="language-toggle",
                color="light",
                outline=True,
                size="sm",
                className="ms-2",
                style={"color": "white", "borderColor": "white"}
            ),
            width="auto"
        ),
    ], className="g-2 ms-auto flex-nowrap mt-3 mt-md-0", align="center")
    
    # Brand/Logo com imagem ESALQ e título em branco
    brand = dbc.Row([
        dbc.Col(
            html.Img(
                src="/assets/images/logo_esalq_2.png",
                height="50px",
                className="d-inline-block align-top me-2",
                style={"objectFit": "contain"}
            ),
            width="auto",
            className="d-none d-md-block"
        ),
        dbc.Col(
            html.Div([
                html.Span("EVAonline",
                         className="navbar-brand-text",
                         style={"fontSize": "24px",
                                "fontWeight": "bold",
                                "color": "white"}),
                html.Br(),
                html.Small(
                    "An online tool for reference EVApotranspiration estimation",
                    className="text-white-50",
                    style={"fontSize": "13px"}
                )
            ]),
            width="auto"
        )
    ], align="center", className="g-2")
    
    return dbc.Navbar(
        dbc.Container([
            html.A(
                brand,
                href=settings.DASH_ROUTES["home"],
                className="navbar-brand",
                style={"textDecoration": "none"}
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                nav_items,
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ], fluid=True),
        color="#2d5016",
        dark=True,
        className="mb-3 py-2 shadow-sm",
        style={"minHeight": "70px"}
    )


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
