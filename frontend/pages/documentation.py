"""
Página de Documentação do EVAonline.
"""
import dash_bootstrap_components as dbc
from dash import html


def layout():
    """
    Layout da página de documentação.
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Documentação do EVAonline",
                         className="text-center mb-4"),
                html.P(
                    "Bem-vindo à documentação do EVAonline. Aqui você "
                    "encontrará informações detalhadas sobre como usar "
                    "a aplicação.",
                    className="lead"
                ),
                html.Hr(),
                html.H2("Funcionalidades Principais"),
                html.Ul([
                    html.Li("Cálculo de Evapotranspiração (ETo)"),
                    html.Li("Visualização de dados meteorológicos"),
                    html.Li("Análise estatística de resultados"),
                    html.Li("Geração de mapas e gráficos")
                ]),
                html.H2("Como Usar"),
                html.P("Para começar, navegue pelas diferentes seções da "
                       "aplicação usando a barra de navegação."),
                html.H2("Suporte"),
                html.P("Para dúvidas ou suporte, entre em contato conosco "
                       "através do e-mail: suporte@evaonline.com")
            ], width=12)
        ])
    ], fluid=True)
