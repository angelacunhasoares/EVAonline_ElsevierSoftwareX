import dash_bootstrap_components as dbc
from dash import html, dcc
from utils.get_translations import get_translations

def layout():
    t = get_translations()
    return dbc.Container([
        html.H1(t["what_is_evaonline_title"]),
        html.P(t["what_is_evaonline_desc"]),
        html.Div([
            dcc.Markdown(r"""
                $$ET_0 = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$
            """)
        ], style={"max-width": "100%", "overflow-x": "auto", "padding": "10px"}),
        html.P(t["what_is_evaonline_desc_explanation"]),
        dbc.Accordion([
            dbc.AccordionItem(
                title=t["why_use_evaonline_title"],
                children=[html.P(t["why_use_evaonline_desc"])]
            ),
            dbc.AccordionItem(
                title=t["features_title"],
                children=[html.P(t["features_desc"])]
            )
        ]),
        dbc.Row([
            dbc.Col(dbc.Button("Home", href="/", color="primary"), width=4),
            dbc.Col(dbc.Button("Read the docs", href="https://github.com", color="primary"), width=4)
        ])
    ])