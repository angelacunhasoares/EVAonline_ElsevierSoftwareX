"""
Configuração e criação do aplicativo Dash.
"""
import os
import sys

# Adicionar o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from config.settings.app_settings import get_settings
from frontend.pages.about import layout
from frontend.pages.dash_eto import create_layout
from frontend.pages.documentation import layout as documentation_layout
from frontend.pages.home import layout as home_layout

settings = get_settings()


def render_page_content(pathname):
    """
    Renderiza o conteúdo da página baseado na URL.
    """
    if pathname == "/" or pathname == "/home":
        # Importar layout da página home
        try:
            return home_layout()
        except ImportError:
            return html.H1("Home Page - Layout não encontrado")
    
    elif pathname == "/eto":
        # Importar layout da página ETo
        try:
            return create_layout()
        except ImportError:
            return html.H1("ETo Calculator Page - Layout não encontrado")
    
    elif pathname == "/about":
        # Importar layout da página About
        try:
            return layout()
        except ImportError:
            return html.H1("About Page - Layout não encontrado")
    
    elif pathname == "/documentation":
        # Importar layout da página Documentation
        try:
            return documentation_layout()
        except ImportError:
            return html.H1("Documentation Page - Layout não encontrado")
    
    else:
        return html.H1("404 - Página não encontrada")


def create_dash_app() -> dash.Dash:
    """
    Cria e configura o aplicativo Dash.
    """
    # Criar aplicativo Dash
    app = dash.Dash(
        __name__,
        requests_pathname_prefix="/",
        assets_folder=settings.DASH_ASSETS_FOLDER,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
        title=settings.PROJECT_NAME
    )
    
    # Configurar layout inicial
    app.layout = html.Div([
        # NavBar
        dbc.NavbarSimple(
            children=[
                dbc.NavItem(
                    dbc.NavLink(
                        "Calculate ETo",
                        href=settings.DASH_ROUTES["eto_calculator"]
                    )
                ),
                dbc.NavItem(
                    dbc.NavLink(
                        "About",
                        href=settings.DASH_ROUTES["about"]
                    )
                ),
                dbc.NavItem(
                    dbc.NavLink(
                        "Documentação",
                        href=settings.DASH_ROUTES["documentation"]
                    )
                ),
                dbc.NavItem(
                    dbc.Button(
                        "English",
                        id="language-toggle",
                        color="light",
                        outline=True,
                        size="sm",
                        className="ms-2"
                    ),
                    className="ms-auto"
                ),
            ],
            brand="EVAonline",
            brand_href=settings.DASH_ROUTES["home"],
            color="primary",
            dark=True,
            className="mb-4"
        ),

        # Sistema de roteamento
        dcc.Location(id='url', refresh=False),

        # Conteúdo principal
        html.Div(id='page-content')
    ])

    # Callback para roteamento
    @app.callback(
        dash.dependencies.Output('page-content', 'children'),
        [dash.dependencies.Input('url', 'pathname')]
    )
    def display_page(pathname):
        return render_page_content(pathname)

    # Callback para alternar idioma
    @app.callback(
        dash.dependencies.Output('language-toggle', 'children'),
        [dash.dependencies.Input('language-toggle', 'n_clicks')]
    )
    def toggle_language(n_clicks):
        if n_clicks and n_clicks % 2 == 1:
            return "English"
        return "Portuguese"

    # Callback para obter geolocalização
    @app.callback(
        dash.dependencies.Output('geolocation', 'update_now'),
        [dash.dependencies.Input('get-location-btn', 'n_clicks')]
    )
    def update_geolocation(n_clicks):
        if n_clicks:
            return True
        return False

    # Callback para exibir informações de localização
    @app.callback(
        dash.dependencies.Output('location-info', 'children'),
        [dash.dependencies.Input('geolocation', 'local_date'),
         dash.dependencies.Input('geolocation', 'position')]
    )
    def display_location(local_date, position):
        if position and isinstance(position, dict):
            # position é um dicionário com chaves 'lat' e 'lon'
            lat = position.get('lat', 0)
            lon = position.get('lon', 0)
            return f"📍 Latitude: {lat:.6f}, Longitude: {lon:.6f}"
        return "Clique em 'Obter Localização' para ver sua posição."

    # Callback para atualizar marcador de localização do usuário
    @app.callback(
        dash.dependencies.Output('user-location-marker', 'position'),
        [dash.dependencies.Input('geolocation', 'position')]
    )
    def update_user_marker(position):
        if position and isinstance(position, dict):
            # position é um dicionário com chaves 'lat' e 'lon'
            lat = position.get('lat', 0)
            lon = position.get('lon', 0)
            return [lat, lon]
        return [0, 0]

    # Callback para cliques no mapa
    @app.callback(
        dash.dependencies.Output('click-info', 'children'),
        [dash.dependencies.Input('map', 'clickData')]
    )
    def display_click_info(clickData):
        if clickData and 'latlng' in clickData:
            lat = clickData['latlng']['lat']
            lng = clickData['latlng']['lng']
            return f"🎯 Latitude: {lat:.6f}, Longitude: {lng:.6f}"
        return "Clique em qualquer ponto do mapa para ver as coordenadas."

    return app


if __name__ == '__main__':
    app = create_dash_app()
    app.run(
        debug=True,
        host='127.0.0.1',
        port=8050
    )
