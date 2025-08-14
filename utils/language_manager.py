from dash import dcc, html
from dash.dependencies import Input, Output
import os
from utils.get_translations import get_translations

def init_language(app):
    # Armazena o idioma atual no dcc.Store
    app.layout = html.Div([
        dcc.Store(id="language-store", data=os.getenv("LANGUAGE", "pt")),
        app.layout
    ])

    @app.callback(
        Output("language-store", "data"),
        Input("language-toggle", "n_clicks"),
        prevent_initial_call=True
    )
    def switch_language(n_clicks):
        if n_clicks:
            current_lang = os.getenv("LANGUAGE", "pt")
            new_lang = "en" if current_lang == "pt" else "pt"
            os.environ["LANGUAGE"] = new_lang
            return new_lang
        return os.getenv("LANGUAGE", "pt")

    return get_translations()