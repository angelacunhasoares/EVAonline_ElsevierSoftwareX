"""
Configuração e criação do aplicativo Dash.
"""
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from config.settings.app_settings import get_settings

settings = get_settings()

def create_dash_app() -> dash.Dash:
    """
    Cria e configura o aplicativo Dash.
    """
    # Criar aplicativo Dash
    app = dash.Dash(
        __name__,
        requests_pathname_prefix=settings.DASH_REQUESTS_PATHNAME_PREFIX,
        assets_folder=settings.DASH_ASSETS_FOLDER,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
        title=settings.PROJECT_NAME
    )

    from frontend.routes import create_navbar, render_page_content
    
    # Configurar layout inicial
    app.layout = html.Div([
        # NavBar
        create_navbar(),
        
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

    # Importar e registrar callbacks adicionais
    from frontend.callbacks import register_callbacks
    register_callbacks(app)

    return app
