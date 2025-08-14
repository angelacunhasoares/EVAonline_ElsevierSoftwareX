import json
from datetime import date, timedelta
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import pandas as pd
import plotly.graph_objects as go
from loguru import logger
from src.map_generator import create_interactive_map
from src.results_tables import display_results_table

from src.results_graphs import (
    plot_correlation,
    plot_eto_vs_radiation,
    plot_eto_vs_temperature,
    plot_heatmap,
    plot_temp_rad_prec,
)
from src.results_statistical import (
    display_correlation_matrix,
    display_cumulative_distribution,
    display_daily_data,
    display_descriptive_stats,
    display_normality_test,
    display_eto_summary,
)

from src.results_statistical import display_eto_summary
from utils.get_translations import get_translations
from utils.session_utils import reset_state
from api.openmeteo import get_openmeteo_elevation
from utils.data_utils import load_matopiba_data
import requests

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Configurar logging com Loguru
logger = logger.bind(name="eto_dashboard")


# Layout
def create_layout(lang: str = "pt"):
    t = get_translations(lang)
    return dbc.Container([
        html.H3(t["calculate_eto"], className="mt-3", style={"color": "#005B99"}),
        
        # Seletor de idioma
        dcc.Dropdown(
            id="language-selector",
            options=[
                {"label": "Português", "value": "pt"},
                {"label": "English", "value": "en"}
            ],
            value=lang,
            style={"width": "200px", "margin": "10px"}
        ),
        
        # Instruções
        dbc.Accordion([
            dbc.AccordionItem([
                html.P(t["instruction_1"]),
                html.P(t["instruction_2"]),
                html.P(t["instruction_3"]),
                html.P(t["instruction_4"])
            ], title=t["instructions"])
        ], start_collapsed=True),
        
        # Modo de cálculo
        html.Hr(),
        html.H5(t["select_mode"], className="mt-3"),
        dcc.RadioItems(
            id="calculation-mode",
            options=[
                {"label": t["global_mode"], "value": "Global"},
                {"label": t["matopiba_mode"], "value": "MATOPIBA"}
            ],
            value="Global",
            labelStyle={"display": "block"}
        ),
        
        # Coordenadas e parâmetros
        dbc.Row([
            # Coluna de coordenadas/mapa
            dbc.Col([
                html.Div(id="coord-input-section")
            ], width=6),
            
            # Coluna de parâmetros
            dbc.Col([
                html.H5(t["confirmation_params"], className="mt-3", style={"color": "#005B99"}),
                dcc.Dropdown(
                    id="data-source",
                    options=[
                        {"label": "NASA POWER", "value": "NASA POWER"},
                        {"label": "Open-Meteo Archive", "value": "Open-Meteo Archive"},
                        {"label": "Open-Meteo Forecast", "value": "Open-Meteo Forecast"},
                        {"label": "Data Fusion", "value": "Data Fusion"}
                    ],
                    placeholder=t["database"],
                    value=None,
                    style={"margin": "10px"}
                ),
                dcc.DatePickerRange(
                    id="date-range",
                    display_format="DD/MM/YYYY",
                    start_date=date.today() - timedelta(days=7),
                    end_date=date.today(),
                    min_date_allowed=date.today() - timedelta(days=365),
                    max_date_allowed=date.today() + timedelta(days=2),
                    style={"margin": "10px"}
                ),
                html.P(id="mode-display"),
                html.P(id="database-display"),
                html.P(id="start-date-display"),
                html.P(id="end-date-display"),
                html.P(id="state-display", style={"display": "none"}),
                html.P(id="city-display", style={"display": "none"}),
                html.P(id="lat-display"),
                html.P(id="lng-display"),
                html.P(id="elevation-display"),
                dcc.Input(
                    id="elevation-input",
                    type="number",
                    min=-1000,
                    max=9000,
                    step=1,
                    placeholder=t["elevation"],
                    style={"width": "100%", "margin": "10px"}
                ),
                dbc.Row([
                    dbc.Col(dbc.Button(t["cancel"], id="cancel-button", color="danger"), width=6),
                    dbc.Col(dbc.Button(t["confirm"], id="confirm-button", color="success"), width=6)
                ], className="mt-3"),
                dbc.Button(t["calculate_eto_button"], id="calculate-eto-button", color="primary", className="mt-3", disabled=True, style={"width": "100%"}),
                html.Div(id="progress-output")
            ], width=6)
        ]),
        
        # Resultados
        html.Hr(),
        html.H3(t["results_location"], className="mt-3", style={"color": "#005B99"}),
        dcc.Tabs([   
            dcc.Tab(label=t["table_and_graphs"], children=[
                dbc.Row([
                    dbc.Col(dcc.Checklist(id="show-table", options=[{"label": t["show_table"], "value": "show_table"}]), width=6),
                    dbc.Col(dcc.Checklist(id="show-graphic", options=[{"label": t["show_graphic"], "value": "show_graphic"}]), width=6)
                ]),
                dbc.Row([
                    dbc.Col(id="table-output", width=6),
                    dbc.Col([
                        dcc.Dropdown(
                            id="graphic-type",
                            options=[
                                {"label": t["eto_vs_temp"], "value": "eto_vs_temp"},
                                {"label": t["eto_vs_rad"], "value": "eto_vs_rad"},
                                {"label": t["temp_rad_prec"], "value": "temp_rad_prec"},
                                {"label": t["heatmap"], "value": "heatmap"},
                                {"label": t["correlation"], "value": "correlation"}
                            ],
                            value="eto_vs_temp",
                            placeholder=t["select_graphic_type"],
                            style={"margin": "10px"}
                        ),
                        html.Div(id="correlation-var", style={"display": "none"}),
                        dcc.Graph(id="graphic-output")
                    ], width=6)
                ]),
                # Adicionar botões de download
                dbc.Row([
                    dbc.Col(dbc.Button(t["download_csv"], id="download-csv-button", color="primary", className="mt-3", style={"width": "100%"}), width=6),
                    dbc.Col(dbc.Button(t["download_excel"], id="download-excel-button", color="primary", className="mt-3", style={"width": "100%"}), width=6)
                ])
            ]),
            dcc.Tab(label=t["statistical_analysis"], children=[
                html.Div(id="stats-output")
            ])
        ]),
        # Adicionar componentes dcc.Download
        dcc.Download(id="download-csv"),
        dcc.Download(id="download-excel"),
        
        # Botões finais
        html.Hr(),
        dbc.Row([
            dbc.Col(dbc.Button(t["clear_all"], id="clear-button", color="secondary", style={"width": "100%"}), width=6),
            dbc.Col(dbc.Button(t["back_to_home"], id="home-button", color="info", style={"width": "100%"}), width=6)
        ], className="mt-3"),
        
        # Armazenamento de estado
        dcc.Store(id="language-store", data=lang),
        dcc.Store(id="eto_result"),
        dcc.Store(id="eto_warnings"),
        dcc.Store(id="selected-coordinates")
    ], fluid=True)


app.layout = create_layout()


# Callbacks
@callback(
    Output("coord-input-section", "children"),
    Input("calculation-mode", "value"),
    Input("language-selector", "value")
)
def update_coord_input(mode, lang):
    t = get_translations(lang)
    if mode == "Global":
        return [
            html.H5(t["global_mode"], className="mt-3", style={"color": "#005B99"}),
            dcc.RadioItems(
                id="coord-option",
                options=[
                    {"label": t["click_to_select"], "value": "click"},
                    {"label": t["adjust_manually"], "value": "manual"}
                ],
                value="click",
                labelStyle={"display": "block"}
            ),
            html.Div(id="coord-input-global")
        ]
    else:  # MATOPIBA
        df, warnings = load_matopiba_data(lang)
        estados = sorted(df["UF"].unique().tolist()) if not df.empty else []
        return [
            html.H5(t["matopiba_mode"], className="mt-3", style={"color": "#005B99"}),
            dcc.RadioItems(
                id="coord-option",
                options=[
                    {"label": t["choose_city"], "value": "city"},
                    {"label": t["adjust_manually"], "value": "manual"}
                ],
                value="city",
                labelStyle={"display": "block"}
            ),
            html.Div(id="coord-input-matopiba"),
            dcc.Dropdown(id="estado", options=[{"label": e, "value": e} for e in estados], placeholder=t["choose_state"], style={"margin": "10px"}),
            html.Div(id="cidade-container")
        ]


@callback(
    Output("coord-input-global", "children"),
    Input("coord-option", "value"),
    Input("calculation-mode", "value"),
    Input("language-selector", "value")
)
def update_global_coord_input(coord_option, mode, lang):
    t = get_translations(lang)
    if mode != "Global":
        return []
    if coord_option == "click":
        return [
            dl.Map(
                [dl.TileLayer(), create_interactive_map()],
                id="map",
                center=[0, 0],
                zoom=1,
                style={"width": "100%", "height": "50vh"}
            ),
            html.P(id="selected-coords")
        ]
    else:
        return [
            dbc.Row([
                dbc.Col(dcc.Input(id="lat-input", type="number", placeholder=t["latitude"], min=-90, max=90, step=0.000001), width=6),
                dbc.Col(dcc.Input(id="lng-input", type="number", placeholder=t["longitude"], min=-180, max=180, step=0.000001), width=6)
            ])
        ]


@callback(
    Output("coord-input-matopiba", "children"),
    Output("cidade-container", "children"),
    Input("coord-option", "value"),
    Input("estado", "value"),
    Input("calculation-mode", "value"),
    Input("language-selector", "value")
)
def update_matopiba_coord_input(coord_option, estado, mode, lang):
    t = get_translations(lang)
    if mode != "MATOPIBA":
        return [], []
    if coord_option == "city":
        df, warnings = load_matopiba_data(lang)
        cidades = sorted(df[df["UF"] == estado]["CITY"].tolist()) if estado and not df.empty else []
        cidade_dropdown = dcc.Dropdown(
            id="cidade",
            options=[{"label": c, "value": c} for c in cidades],
            placeholder=t["choose_city"],
            disabled=not estado,
            style={"margin": "10px"}
        )
        return [], cidade_dropdown
    else:
        return [
            dbc.Row([
                dbc.Col(dcc.Input(id="lat-input", type="number", placeholder=t["latitude"], value=-8.5, min=-14.5, max=-2.5, step=0.1), width=6),
                dbc.Col(dcc.Input(id="lng-input", type="number", placeholder=t["longitude"], value=-45.75, min=-50.0, max=-41.5, step=0.1), width=6)
            ])
        ], []


@callback(
    Output("selected-coords", "children"),
    Output("lat-display", "children"),
    Output("lng-display", "children"),
    Output("elevation-display", "children"),
    Output("state-display", "children"),
    Output("city-display", "children"),
    Output("state-display", "style"),
    Output("city-display", "style"),
    Output("calculate-eto-button", "disabled"),
    Output("selected-coordinates", "data"),
    Input("map", "click_lat_lng"),
    Input("lat-input", "value"),
    Input("lng-input", "value"),
    Input("elevation-input", "value"),
    Input("estado", "value"),
    Input("cidade", "value"),
    Input("calculation-mode", "value"),
    Input("coord-option", "value"),
    Input("language-selector", "value"),
    State("selected-coordinates", "data"),
    prevent_initial_call=True
)
async def update_coordinates(click_lat_lng, lat_input, lng_input, elevation_input, estado, cidade, mode, coord_option, lang, coords_from_home):
    t = get_translations(lang)
    lat, lng, elevation = None, None, None
    state_display, city_display = t["state"], t["city"]
    state_style, city_style = {"display": "none"}, {"display": "none"}
    
    if mode == "Global" and coords_from_home:
        lat = coords_from_home.get("lat")
        lng = coords_from_home.get("lng")
        elevation, elevation_warnings = await get_openmeteo_elevation(lat, lng)
    
    if mode == "Global" and coord_option == "click" and click_lat_lng:
        lat, lng = click_lat_lng
        elevation, elevation_warnings = await get_openmeteo_elevation(lat, lng)
    elif mode == "Global" and coord_option == "manual":
        lat, lng = lat_input, lng_input
        elevation, elevation_warnings = await get_openmeteo_elevation(lat, lng) if elevation_input is None else (elevation_input, [])
    elif mode == "MATOPIBA" and coord_option == "city" and estado and cidade:
        df, warnings = load_matopiba_data(lang)
        cidade_info = df[(df["UF"] == estado) & (df["CITY"] == cidade)]
        if not cidade_info.empty:
            lat, lng, elevation = cidade_info.iloc[0][["LATITUDE", "LONGITUDE", "HEIGHT"]]
            state_display, city_display = estado, cidade
            state_style, city_style = {"display": "block"}, {"display": "block"}
    elif mode == "MATOPIBA" and coord_option == "manual":
        lat, lng = lat_input, lng_input
        elevation, elevation_warnings = await get_openmeteo_elevation(lat, lng) if elevation_input is None else (elevation_input, [])
    
    valid = (
        lat is not None and lng is not None and elevation is not None and
        -90 <= lat <= 90 and -180 <= lng <= 180 and
        (mode != "MATOPIBA" or (-14.5 <= lat <= -2.5 and -50.0 <= lng <= -41.5))
    )
    
    coords_data = {"lat": lat, "lng": lng, "elev": elevation} if valid else None
    
    return (
        f"{t['coords_captured']}: {lat:.6f}, {lng:.6f}, {t['elevation']}: {elevation:.2f}m" if valid else "",
        f"🌐 {t['latitude']}: {lat:.6f}" if lat else f"🌐 {t['latitude']}: Não selecionado",
        f"🌐 {t['longitude']}: {lng:.6f}" if lng else f"🌐 {t['longitude']}: Não selecionado",
        f"📏 {t['elevation']}: {elevation:.2f}m" if elevation else f"📏 {t['elevation']}: Não selecionado",
        f"🌎 {t['state']}: {state_display}",
        f"🌆 {t['city']}: {city_display}",
        state_style,
        city_style,
        not valid,
        coords_data
    )


@callback(
    Output("mode-display", "children"),
    Output("database-display", "children"),
    Output("start-date-display", "children"),
    Output("end-date-display", "children"),
    Output("progress-output", "children", allow_duplicate=True),
    Input("confirm-button", "n_clicks"),
    State("calculation-mode", "value"),
    State("data-source", "value"),
    State("date-range", "start_date"),
    State("date-range", "end_date"),
    State("language-selector", "value"),
    prevent_initial_call=True
)
def update_params(confirm_clicks, mode, data_source, start_date, end_date, lang):
    t = get_translations(lang)
    progress_content = []
    
    if confirm_clicks:
        data_inicial = pd.to_datetime(start_date).strftime("%d/%m/%Y") if start_date else None
        data_final = pd.to_datetime(end_date).strftime("%d/%m/%Y") if end_date else None
        
        # Validar parâmetros
        hoje = date.today()
        um_ano_atras = hoje - timedelta(days=365)
        limite_futuro = hoje + timedelta(days=2)
        
        if not data_source:
            progress_content.append(html.P(t["no_database_selected"]))
        if not data_inicial or not data_final:
            progress_content.append(html.P(t["no_dates_selected"]))
        else:
            try:
                data_inicial_dt = pd.to_datetime(data_inicial, format="%d/%m/%Y")
                data_final_dt = pd.to_datetime(data_final, format="%d/%m/%Y")
                delta = (data_final_dt - data_inicial_dt).days + 1
                if data_final_dt < data_inicial_dt:
                    progress_content.append(html.P(t["invalid_date_range"]))
                elif not (7 <= delta <= 15):
                    progress_content.append(html.P(t["invalid_period"].format(delta)))
                elif data_inicial_dt < um_ano_atras:
                    progress_content.append(html.P(t["date_too_old"].format(um_ano_atras.strftime("%d/%m/%Y"))))
                elif data_final_dt > limite_futuro:
                    progress_content.append(html.P(t["date_too_future"].format(limite_futuro.strftime("%d/%m/%Y"))))
                else:
                    progress_content.append(html.P(t["valid_period"].format(delta)))
            except ValueError as e:
                progress_content.append(html.P(t["invalid_date_format"].format(str(e))))
        
        return (
            f"**{t['calculation_mode']}:** {mode}",
            f"📂 **{t['database']}:** {data_source if data_source else 'Não selecionado'}",
            f"📆 **{t['start_date']}:** {data_inicial if data_inicial else 'Não selecionado'}",
            f"📆 **{t['end_date']}:** {data_final if data_final else 'Não selecionado'}",
            html.Ul([html.Li(p) for p in progress_content]) if progress_content else html.P(t["no_warnings"])
        )
    
    return (
        f"**{t['calculation_mode']}:** {mode}",
        f"📂 **{t['database']}:** Não selecionado",
        f"📆 **{t['start_date']}:** Não selecionado",
        f"📆 **{t['end_date']}:** Não selecionado",
        html.P(t["no_warnings"])
    )


@callback(
    Output("table-output", "children"),
    Output("graphic-output", "figure"),
    Output("correlation-var", "children"),
    Output("correlation-var", "style"),
    Output("progress-output", "children", allow_duplicate=True),
    Output("eto_result", "data"),
    Output("eto_warnings", "data"),
    Output("stats-output", "children"),  # Nova saída
    Input("calculate-eto-button", "n_clicks"),
    State("show-table", "value"),
    State("show-graphic", "value"),
    State("graphic-type", "value"),
    State("calculation-mode", "value"),
    State("data-source", "value"),
    State("date-range", "start_date"),
    State("date-range", "end_date"),
    State("selected-coordinates", "data"),
    State("estado", "value"),
    State("cidade", "value"),
    State("language-selector", "value"),
    prevent_initial_call=True
)
async def update_results(n_clicks, show_table, show_graphic, graphic_type, mode, data_source, start_date, end_date, coords, estado, cidade, lang):
    from src.results_tables import display_results_table
    from src.results_graphs import plot_eto_vs_temperature, plot_eto_vs_radiation, plot_temp_rad_prec, plot_heatmap, plot_correlation
    from src.results_statistical import display_descriptive_stats, display_normality_test, display_correlation_matrix, display_eto_summary, display_trend_analysis, display_seasonality_test, display_cumulative_distribution
    from utils.get_translations import get_translations
    from loguru import logger
    import requests
    import plotly.graph_objects as go
    from dash import dash, html, dcc

    t = get_translations(lang)
    table_content = []
    fig = go.Figure()
    corr_var_input = []
    corr_var_style = {"display": "none"}
    progress_content = []
    stats_content = []

    if n_clicks and coords and data_source and start_date and end_date:
        try:
            start_date_formatted = pd.to_datetime(start_date).strftime("%Y-%m-%d")
            end_date_formatted = pd.to_datetime(end_date).strftime("%Y-%m-%d")

            response = requests.get(
                f"http://localhost:8000/calculate_eto?lat={coords['lat']}&lng={coords['lng']}&elevation={coords['elev']}&database={data_source}&start_date={start_date_formatted}&end_date={end_date_formatted}&estado={estado}&cidade={cidade}"
            )
            data = response.json()

            if "error" in data:
                progress_content.append(html.P(f"{t['error']}: {data['error']}"))
                return table_content, fig, corr_var_input, corr_var_style, html.Ul([html.Li(p) for p in progress_content]), [], [], []

            df = pd.DataFrame(data["data"])
            warnings = data["warnings"]
            progress_content.extend([html.P(w) for w in warnings])

            eto_result = df.to_dict("records")
            eto_warnings = warnings

            if show_table and not df.empty:
                table_content = [
                    display_results_table(df, lang=lang),
                    html.Hr(),
                    html.H5(t["progress"]),
                    html.Ul([html.Li(w) for w in warnings]) if warnings else html.P(t["no_warnings"])
                ]

            if show_graphic and not df.empty:
                df_graph = df.copy()
                df_graph["date"] = pd.to_datetime(df_graph["date"]).dt.strftime("%d/%m/%Y")
                df_graph = df_graph.round(2)

                if graphic_type == "eto_vs_temp":
                    fig = plot_eto_vs_temperature(df_graph, lang=lang)
                elif graphic_type == "eto_vs_rad":
                    fig = plot_eto_vs_radiation(df_graph, lang=lang)
                elif graphic_type == "temp_rad_prec":
                    fig = plot_temp_rad_prec(df_graph, lang=lang)
                elif graphic_type == "heatmap":
                    fig = plot_heatmap(df_graph, lang=lang)
                elif graphic_type == "correlation":
                    corr_var_input = dcc.Dropdown(
                        id="corr-var",
                        options=[{"label": t.get(col.lower(), col), "value": col} for col in df_graph.drop(columns=["date", "ETo", "PRECTOTCORR"]).columns],
                        value=df_graph.drop(columns=["date", "ETo", "PRECTOTCORR"]).columns[0]
                    )
                    corr_var_style = {"display": "block"}
                    fig = plot_correlation(df_graph, corr_var_input.value, lang=lang)

                mean_eto = df_graph["ETo"].mean().round(2)
                table_content.append(html.P(f"**{t['mean_eto']}:** {mean_eto} mm/day"))

            # Análises estatísticas
            if not df.empty:
                stats_content = [
                    display_daily_data(df, lang=lang),
                    html.Hr(),
                    display_descriptive_stats(df, lang=lang),
                    html.Hr(),
                    display_normality_test(df, lang=lang),
                    html.Hr(),
                    display_correlation_matrix(df, lang=lang),
                    html.Hr(),
                    display_eto_summary(df, lang=lang),
                    html.Hr(),
                    display_trend_analysis(df, lang=lang),
                    html.Hr(),
                    display_seasonality_test(df, lang=lang),
                    html.Hr(),
                    display_cumulative_distribution(df, lang=lang)
                ]

            return (
                table_content,
                fig,
                corr_var_input,
                corr_var_style,
                html.Ul([html.Li(p) for p in progress_content]) if progress_content else html.P(t["no_warnings"]),
                eto_result,
                eto_warnings,
                stats_content
            )

        except Exception as e:
            logger.error(f"Erro ao atualizar resultados: {str(e)}")
            progress_content.append(html.P(f"{t['error']}: {str(e)}"))
            return table_content, fig, corr_var_input, corr_var_style, html.Ul([html.Li(p) for p in progress_content]), [], [], []

    return table_content, fig, corr_var_input, corr_var_style, html.P(t["no_warnings"]), [], [], []


@callback(
    Output("stats-table-output", "children"),
    Output("cumulative-dist-output", "children"),
    Input("stats-table-type", "value"),
    Input("show-cumulative-dist", "value"),
    Input("eto_result", "data"),
    Input("language-selector", "value")
)
def update_stats(stats_table_type, show_cumulative, eto_result, lang):
    t = get_translations(lang)
    if not eto_result:
        return html.P(t["calculate_first"]), []
    
    result_df = pd.DataFrame(eto_result)
    stats_content = []
    if stats_table_type == "daily_data":
        stats_content = [display_daily_data(result_df)]
    else:
        stats_content = [
            display_descriptive_stats(result_df),
            display_normality_test(result_df),
            display_correlation_matrix(result_df),
            display_eto_summary(result_df)
        ]
    
    cumulative_content = display_cumulative_distribution(result_df) if show_cumulative else []
    return stats_content, cumulative_content


@callback(
    Output("url", "pathname"),
    Output("language-store", "data"),
    Output("eto_result", "data"),
    Output("eto_warnings", "data"),
    Output("selected-coordinates", "data"),
    Input("home-button", "n_clicks"),
    Input("clear-button", "n_clicks"),
    Input("cancel-button", "n_clicks"),
    Input("confirm-button", "n_clicks"),
    Input("language-selector", "value"),
    State("calculation-mode", "value"),
    State("selected-coordinates", "data"),
    State("data-source", "value"),
    State("date-range", "start_date"),
    State("date-range", "end_date"),
    State("estado", "value"),
    State("cidade", "value")
)
def navigate_or_reset(home_clicks, clear_clicks, cancel_clicks, confirm_clicks, lang, mode, coords, data_source, start_date, end_date, estado, cidade):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, lang, dash.no_update, dash.no_update, dash.no_update
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id == "home-button":
        return "/", lang, dash.no_update, dash.no_update, dash.no_update
    elif button_id in ["clear-button", "cancel-button"]:
        reset_state(["eto_result", "eto_warnings", "selected-coordinates"])
        return "/eto", lang, None, None, None
    elif button_id == "confirm-button":
        return dash.no_update, lang, dash.no_update, dash.no_update, dash.no_update
    elif button_id == "language-selector":
        return dash.no_update, lang, dash.no_update, dash.no_update, dash.no_update
    return dash.no_update, lang, dash.no_update, dash.no_update, dash.no_update


@callback(
    Output("download-csv", "data"),
    Output("download-excel", "data"),
    Input("download-csv-button", "n_clicks"),
    Input("download-excel-button", "n_clicks"),
    State("eto_result", "data"),
    State("language-selector", "value"),
    prevent_initial_call=True
)
def download_data(csv_clicks, excel_clicks, eto_result, lang):
    from utils.get_translations import get_translations
    from loguru import logger
    import io
    import pandas as pd
    from dash import dcc

    t = get_translations(lang)
    
    if not eto_result:
        logger.warning("Tentativa de download sem dados disponíveis")
        return None, None

    try:
        # Criar DataFrame e formatar
        df = pd.DataFrame(eto_result)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
        df = df[["date", "T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "ETo"]]
        df = df.round(2).rename(columns={
            "date": t["date"],
            "T2M_MAX": t["temp_max"],
            "T2M_MIN": t["temp_min"],
            "RH2M": t["humidity"],
            "WS2M": t["wind_speed"],
            "ALLSKY_SFC_SW_DWN": t["radiation"],
            "PRECTOTCORR": t["precipitation"],
            "ETo": t["eto"]
        })

        ctx = dash.callback_context
        if not ctx.triggered:
            return None, None

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "download-csv-button":
            logger.info("Download de CSV iniciado")
            return dcc.send_data_frame(df.to_csv, "table_eto_results.csv", index=False), None
        elif button_id == "download-excel-button":
            logger.info("Download de Excel iniciado")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="ET₀ Results", index=False)
            excel_data = output.getvalue()
            return None, dict(content=excel_data, filename="table_eto_results.xlsx", type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        return None, None

    except Exception as e:
        logger.error(f"Erro ao processar download: {str(e)}")
        return None, None


@callback(
    Output("deficit-chart-output", "children"),
    Output("balance-chart-output", "children"),
    Input("deficit-chart-checklist", "value"),
    Input("balance-chart-checklist", "value"),
    State("eto_result", "data"),
    State("language-selector", "value"),
    prevent_initial_call=True
)
def update_eto_summary_charts(deficit_checklist, balance_checklist, eto_result, lang):
    t = get_translations(lang)
    if not eto_result:
        return html.P(t["no_data"]), html.P(t["no_data"])

    df = pd.DataFrame(eto_result)
    summary_content = display_eto_summary(df, lang=lang)
    
    deficit_output = [dcc.Graph(id="deficit-chart", figure=summary_content.children[-4].figure)] if "show_deficit" in deficit_checklist else []
    balance_output = [dcc.Graph(id="balance-chart", figure=summary_content.children[-2].figure)] if "show_balance" in balance_checklist else []
    
    return deficit_output, balance_output

@callback(
    Output("progress-output", "children", allow_duplicate=True),
    Input("download-csv", "data"),
    Input("download-excel", "data"),
    State("language-selector", "value"),
    prevent_initial_call=True
)
def update_download_progress(csv_data, excel_data, lang):
    t = get_translations(lang)
    if csv_data or excel_data:
        return html.P(t["download_started"])
    return dash.no_update


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)