"""
EVAonline ETo Dashboard com Mapas de Calor e Análises

Este módulo implementa a página de cálculo e visualização de evapotranspiração (ETo) do EVAonline.
Permite que os usuários:
1. Visualizem mapas de calor de ETo para o Matopiba atualizado 3x por dia
2. Analisem séries temporais de dados de ETo
3. Comparem diferentes fontes de dados (NASA POWER, NOAA, Open-Meteo)
4. Realizem análises estatísticas
5. Exportem dados em vários formatos (CSV, Excel, GeoJSON)

O sistema usa:
- dash-leaflet para mapas de calor e camadas GeoJSON
- PostgreSQL com PostGIS para armazenamento de dados geoespaciais
- Algoritmo de fusão de dados de múltiplas fontes
"""

# Standard library imports
import io
import os
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import parse_qs

# Third-party imports
import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
from dash import dcc, html, Input, Output, State, callback, no_update
from dotenv import load_dotenv
from loguru import logger

# Local imports
from components.navbar import render_navbar_bootswatch
from components.footer import render_footer_bootswatch
from backend.core.map_results.map_generator import create_interactive_map
from backend.core.results_graphs import (
    plot_correlation,
    plot_eto_vs_radiation,
    plot_eto_vs_temperature,
    plot_heatmap,
    plot_temp_rad_prec
)
from backend.core.results_statistical import (
    display_correlation_matrix,
    display_cumulative_distribution,
    display_daily_data,
    display_descriptive_stats,
    display_eto_summary,
    display_normality_test,
    display_seasonality_test,
    display_trend_analysis
)
from backend.core.results_tables import display_results_table
from utils.data_utils import load_matopiba_data
from utils.get_translations import get_translations

# --- Configurações e Constantes ---

# Carrega variáveis de ambiente
load_dotenv()

# Configurações da API
API_CONFIG = {
    'url': os.getenv("API_URL", "http://api:8000"),
    'timeout': int(os.getenv("API_TIMEOUT", "10")),
    'retry_attempts': int(os.getenv("API_RETRY_ATTEMPTS", "3"))
}

# Configurações de datas
DATE_CONFIG = {
    'max_days_past': int(os.getenv("MAX_DAYS_PAST", "365")),
    'max_days_future': int(os.getenv("MAX_DAYS_FUTURE", "1"))
}

# Cache para traduções
_translations_cache: Dict[str, dict] = {}

def get_translations_cached(lang: str = "pt") -> dict:
    """
    Busca traduções da API com cache e fallback para arquivo local.
    
    Args:
        lang: Código do idioma (pt/en)
    
    Returns:
        dict: Dicionário com as traduções
        
    Note:
        Usa cache em memória para reduzir chamadas à API
    """
    if lang in _translations_cache:
        return _translations_cache[lang]
        
    try:
        response = requests.get(
            f"{API_CONFIG['url']}/api/translations/{lang}",
            timeout=API_CONFIG['timeout']
        )
        response.raise_for_status()
        translations = response.json()
        
        # Armazena no cache
        _translations_cache[lang] = translations
        logger.info(f"Traduções carregadas da API para '{lang}'")
        
        return translations
        
    except requests.Timeout:
        logger.warning(f"Timeout ao buscar traduções para '{lang}'")
        return get_translations(lang)
        
    except requests.RequestException as e:
        logger.error(
            f"Erro ao buscar traduções para '{lang}'. "
            f"Usando fallback local. Erro: {str(e)}"
        )
        return get_translations(lang)

# --- Gestão de Estado ---

class EToState:
    """
    Classe para gerenciar o estado da aplicação ETo.
    
    Attributes:
        DEFAULT_DATES (dict): Datas padrão para o período de cálculo
        REQUIRED_FIELDS (list): Campos obrigatórios para cálculo
        VALID_MODES (list): Modos de cálculo válidos
    """
    
    DEFAULT_DATES = {
        'start': date.today() - timedelta(days=7),
        'end': date.today(),
        'min_past': timedelta(days=DATE_CONFIG['max_days_past']),
        'max_future': timedelta(days=DATE_CONFIG['max_days_future'])
    }
    
    REQUIRED_FIELDS = ['lat', 'lng', 'elev', 'database', 'start_date', 'end_date']
    VALID_MODES = ['Global', 'MATOPIBA']
    
    @staticmethod
    def validate_coordinates(coords: dict) -> Tuple[bool, Optional[str]]:
        """
        Valida as coordenadas fornecidas.
        
        Args:
            coords: Dicionário com lat, lng e elev
            
        Returns:
            bool: True se válido, False caso contrário
            str: Mensagem de erro se inválido, None se válido
        """
        if not coords or not all(k in coords for k in ['lat', 'lng', 'elev']):
            return False, "Coordenadas incompletas"
            
        try:
            lat, lng, elev = coords['lat'], coords['lng'], coords['elev']
            if not (-90 <= lat <= 90):
                return False, "Latitude inválida"
            if not (-180 <= lng <= 180):
                return False, "Longitude inválida"
            if not (0 <= elev <= 8848):  # Altura do Monte Everest
                return False, "Elevação inválida"
            return True, None
        except (TypeError, ValueError):
            return False, "Valores de coordenadas inválidos"
    
    @staticmethod
    def validate_dates(start_date: str, end_date: str) -> Tuple[bool, Optional[str]]:
        """
        Valida o período selecionado.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            bool: True se válido, False caso contrário
            str: Mensagem de erro se inválido, None se válido
        """
        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
            
            if end < start:
                return False, "Data final anterior à inicial"
                
            min_date = date.today() - EToState.DEFAULT_DATES['min_past']
            max_date = date.today() + EToState.DEFAULT_DATES['max_future']
            
            if start < min_date or end > max_date:
                return False, "Período fora do intervalo permitido"
                
            return True, None
        except ValueError:
            return False, "Formato de data inválido"

# --- Layout da Página ---

def create_layout(lang: str = "pt") -> dbc.Container:
    """
    Cria o layout completo e modular do dashboard de ETo.
    
    Args:
        lang: Código do idioma (pt/en)
        
    Returns:
        dbc.Container: Layout completo da página
    """
    t = get_translations_cached(lang)
    
    return dbc.Container([
        # Componentes de estado e localização
        dcc.Location(id='eto-url', refresh=False),
        dcc.Store(id='eto-language-store', data=lang),
        dcc.Store(id='eto-selected-coordinates'),
        dcc.Store(id='eto-result-data'),
        dcc.Store(id='eto-warnings-data'),
        dcc.Store(id='eto-validation-errors'),

        # Cabeçalho e instruções
        html.H3(t["calculate_eto"], className="mt-4 mb-3 text-primary"),
        dbc.Accordion([
            dbc.AccordionItem([html.P(t[f"instruction_{i}"]) for i in range(1, 5)], title=t["instructions"])
        ], start_collapsed=True, className="mb-4"),

        # Seção de Parâmetros
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5(t["select_mode"], className="card-title"),
                dbc.RadioItems(id="calculation-mode", options=[
                    {"label": t["global_mode"], "value": "Global"},
                    {"label": t["matopiba_mode"], "value": "MATOPIBA"}
                ], value="Global", className="mb-3"),
                html.Div(id="coord-input-section")
            ])), md=6, className="mb-4"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5(t["confirmation_params"], className="card-title"),
                dcc.Dropdown(id="data-source", options=[{"label": "NASA POWER", "value": "nasa_power"}], placeholder=t["database"]),
                dcc.DatePickerRange(id="date-range", display_format="DD/MM/YYYY", start_date=date.today() - timedelta(days=7), end_date=date.today(), min_date_allowed=date.today() - timedelta(days=365), max_date_allowed=date.today() + timedelta(days=1), className="mt-3 mb-3"),
                html.Div(id="params-display", className="text-muted small border-start border-2 ps-2"),
                dbc.Button(t["calculate_eto_button"], id="calculate-eto-button", color="primary", className="mt-3 w-100", disabled=True),
                dbc.Spinner(html.Div(id="progress-output", className="mt-2"))
            ])), md=6, className="mb-4"),
        ]),
        
        # Seção de Resultados (inicialmente oculta)
        html.Div(id="results-section", style={'display': 'none'})
    ], fluid=True)


# --- CALLBACKS ---

# Callback 1: Preenche as coordenadas a partir da URL
@callback(
    Output('eto-selected-coordinates', 'data'),
    Output('calculation-mode', 'value'),
    Input('eto-url', 'search')
)
def populate_from_url(search: str) -> tuple:
    """
    Lê os parâmetros da URL para preencher as coordenadas iniciais.
    
    Args:
        search: String de busca da URL
        
    Returns:
        tuple: (coordenadas, modo de cálculo)
    """
    if not search:
        return no_update, no_update
        
    try:
        # Extrai parâmetros da URL
        params = parse_qs(search.lstrip('?'))
        lat_str = params.get('lat', [None])[0]
        lng_str = params.get('lng', [None])[0]
        
        if not (lat_str and lng_str):
            return no_update, no_update
            
        # Converte e valida coordenadas
        lat, lng = float(lat_str), float(lng_str)
        is_valid, error_msg = EToState.validate_coordinates(
            {'lat': lat, 'lng': lng, 'elev': 0}
        )
        
        if not is_valid:
            logger.error(f"Coordenadas inválidas na URL: {error_msg}")
            return no_update, no_update
            
        # Busca elevação via API
        try:
            response = call_api_with_retry(
                "/api/get_elevation",
                params={"lat": lat, "lng": lng}
            )
            elev = response.json().get("data", {}).get("elevation")
            
            if elev is not None:
                return {'lat': lat, 'lng': lng, 'elev': elev}, 'Global'
                
        except requests.RequestException as e:
            logger.error(f"Erro ao buscar elevação: {str(e)}")
            
    except (ValueError, TypeError) as e:
        logger.error(f"Erro ao processar coordenadas da URL: {str(e)}")
        
    return no_update, no_update


# --- Funções de API ---

def call_api_with_retry(
    endpoint: str,
    params: dict = None,
    method: str = "GET",
    max_retries: int = None
) -> requests.Response:
    """
    Faz chamada à API com retry e timeout.
    
    Args:
        endpoint: Endpoint da API (sem a URL base)
        params: Parâmetros da requisição
        method: Método HTTP
        max_retries: Número máximo de tentativas
        
    Returns:
        requests.Response: Resposta da API
        
    Raises:
        requests.RequestException: Se todas as tentativas falharem
    """
    if max_retries is None:
        max_retries = API_CONFIG['retry_attempts']
        
    url = f"{API_CONFIG['url']}{endpoint}"
    timeout = API_CONFIG['timeout']
    
    for attempt in range(max_retries):
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                timeout=timeout
            )
            response.raise_for_status()
            return response
            
        except requests.Timeout:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Timeout na tentativa {attempt + 1}/{max_retries}")
            
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(
                f"Erro na tentativa {attempt + 1}/{max_retries}: {str(e)}"
            )

# --- Callbacks ---

@callback(
    Output("results-section", "children"),
    Output("results-section", "style"),
    Output("progress-output", "children"),
    Output("eto-result-data", "data"),
    Output("eto-warnings-data", "data"),
    Input("calculate-eto-button", "n_clicks"),
    State("eto-selected-coordinates", "data"),
    State("data-source", "value"),
    State("date-range", "start_date"),
    State("date-range", "end_date"),
    State('eto-language-store', 'data'),
    prevent_initial_call=True
)
def execute_eto_calculation(
    n_clicks: int,
    coords: dict,
    data_source: str,
    start_date: str,
    end_date: str,
    lang: str
) -> tuple:
    """
    Executa o cálculo de ETo via API e renderiza os resultados.
    
    Args:
        n_clicks: Número de cliques no botão
        coords: Coordenadas selecionadas
        data_source: Fonte dos dados
        start_date: Data inicial
        end_date: Data final
        lang: Código do idioma
        
    Returns:
        tuple: (layout, estilo, progresso, dados, avisos)
    """
    if not n_clicks:
        return no_update

    t = get_translations_cached(lang)
    
    # Validação de entrada
    is_valid, error_msg = EToState.validate_coordinates(coords)
    if not is_valid:
        return (
            no_update,
            {'display': 'none'},
            dbc.Alert(f"{t['invalid_coords']}: {error_msg}", color="danger"),
            None,
            None
        )
    
    is_valid, error_msg = EToState.validate_dates(start_date, end_date)
    if not is_valid:
        return (
            no_update,
            {'display': 'none'},
            dbc.Alert(f"{t['invalid_dates']}: {error_msg}", color="danger"),
            None,
            None
        )
    
    # Prepara parâmetros
    params = {
        "lat": coords['lat'],
        "lng": coords['lng'],
        "elev": coords['elev'],
        "database": data_source,
        "start_date": start_date,
        "end_date": end_date
    }
    
    try:
        # Faz a chamada à API
        response = call_api_with_retry("/api/calculate_eto", params=params)
        result_data = response.json()

        if "error" in result_data:
            return (
                no_update,
                {'display': 'none'},
                dbc.Alert(f"Erro: {result_data['error']}", color="danger"),
                None,
                None
            )

        df = pd.DataFrame(result_data.get("data", []))
        warnings = result_data.get("warnings", [])

        if df.empty:
            return (
                no_update,
                {'display': 'none'},
                dbc.Alert(t["no_data_found"], color="info"),
                None,
                None
            )

        # Cria o layout dos resultados
        results_layout = create_results_layout(df, t, warnings)
        return (
            results_layout,
            {'display': 'block'},
            [dbc.Alert(w, color="warning") for w in warnings],
            df.to_dict('records'),
            warnings
        )

    except requests.RequestException as e:
        return no_update, {'display': 'none'}, dbc.Alert(t["api_connection_error"], color="danger"), None, None
    except Exception as e:
        error_msg = f"{t['unexpected_error']}: {str(e)}"
        logger.error(f"Erro não esperado no cálculo: {error_msg}")
        return (
            no_update,
            {'display': 'none'},
            dbc.Alert(error_msg, color="danger"),
            None,
            None
        )


def create_results_layout(df: pd.DataFrame, t: dict, warnings: list) -> html.Div:
    """
    Cria o layout da seção de resultados.
    
    Args:
        df: DataFrame com os resultados
        t: Dicionário de traduções
        warnings: Lista de avisos
        
    Returns:
        html.Div: Layout da seção de resultados
    """
    return html.Div([
        html.Hr(),
        html.H3(t["results_location"], className="mt-4 mb-4 text-primary"),
        dcc.Tabs(id="results-tabs", children=[
            create_visualization_tab(t),
            create_statistics_tab(t)
        ])
    ])


def create_visualization_tab(t: dict) -> dcc.Tab:
    """
    Cria a aba de visualização com tabelas e gráficos.
    
    Args:
        t: Dicionário de traduções
        
    Returns:
        dcc.Tab: Aba de visualização
    """
    return dcc.Tab(
        label=t["table_and_graphs"],
        children=[
            # Controles de visualização
            dbc.Row([
                dbc.Col(
                    dbc.Checklist(
                        id="show-table-checklist",
                        options=[{"label": t["show_table"], "value": "show"}],
                        value=['show']
                    ),
                    width="auto"
                ),
                dbc.Col(
                    dbc.Checklist(
                        id="show-graph-checklist",
                        options=[{"label": t["show_graphic"], "value": "show"}],
                        value=['show']
                    ),
                    width="auto"
                ),
            ], className="mt-3"),
            
            # Contêineres de conteúdo
            dbc.Row([
                dbc.Col(html.Div(id="table-container"), md=6),
                dbc.Col(html.Div(id="graph-container"), md=6),
            ], className="mt-3"),
            
            # Botões de download
            create_download_buttons(t)
        ]
    )


def create_statistics_tab(t: dict) -> dcc.Tab:
    """
    Cria a aba de análises estatísticas.
    
    Args:
        t: Dicionário de traduções
        
    Returns:
        dcc.Tab: Aba de estatísticas
    """
    return dcc.Tab(
        label=t["statistical_analysis"],
        children=[html.Div(id="stats-container", className="mt-3")]
    )


def create_download_buttons(t: dict) -> dbc.Row:
    """
    Cria os botões de download.
    
    Args:
        t: Dicionário de traduções
        
    Returns:
        dbc.Row: Linha com botões de download
    """
    return dbc.Row(
        dbc.Col(
            html.Div([
                dbc.Button(
                    t["download_csv"],
                    id="download-csv-button",
                    color="secondary",
                    outline=True,
                    size="sm",
                    className="me-2"
                ),
                dbc.Button(
                    t["download_excel"],
                    id="download-excel-button",
                    color="secondary",
                    outline=True,
                    size="sm"
                ),
                dcc.Download(id="download-csv"),
                dcc.Download(id="download-excel"),
            ]),
            width=12,
            className="mt-3"
        )
    )


# Callback 3: Renderiza o conteúdo da aba de Tabela e Gráficos
@callback(
    Output("table-container", "children"),
    Output("graph-container", "children"),
    Input("show-table-checklist", "value"),
    Input("show-graph-checklist", "value"),
    State("eto-result-data", "data"),
    State('eto-language-store', 'data')
)
def render_table_and_graph_content(
    show_table: list,
    show_graph: list,
    eto_data: dict,
    lang: str
) -> tuple:
    """
    Renderiza a tabela e a seção de gráficos com base nos checklists.
    
    Args:
        show_table: Lista com 'show' se tabela deve ser exibida
        show_graph: Lista com 'show' se gráfico deve ser exibido
        eto_data: Dados dos resultados
        lang: Código do idioma
        
    Returns:
        tuple: (conteúdo da tabela, conteúdo do gráfico)
    """
    if not eto_data: return no_update, no_update
    
    t = get_translations_cached(lang)
    df = pd.DataFrame(eto_data)

    table_content = display_results_table(df, lang=lang) if show_table else None
    
    graph_content = None
    if show_graph:
        graph_options = [
            {"label": t["eto_vs_temp"], "value": "eto_vs_temp"},
            {"label": t["eto_vs_rad"], "value": "eto_vs_rad"},
            {"label": t["temp_rad_prec"], "value": "temp_rad_prec"},
            {"label": t["heatmap"], "value": "heatmap"},
            {"label": t["correlation"], "value": "correlation"}
        ]
        graph_content = html.Div([
            dcc.Dropdown(id="graphic-type-dropdown", options=graph_options, value="eto_vs_temp", clearable=False),
            dcc.Graph(id="main-graph-output", className="mt-2")
        ])
        
    return table_content, graph_content


# Callback 4: Atualiza o gráfico principal com base na seleção do dropdown
@callback(
    Output("main-graph-output", "figure"),
    Input("graphic-type-dropdown", "value"),
    State("eto-result-data", "data"),
    State('eto-language-store', 'data')
)
def update_main_graph(graph_type, eto_data, lang):
    """Atualiza a figura do gráfico com base na opção selecionada."""
    if not eto_data: return go.Figure()

    df = pd.DataFrame(eto_data)
    
    plot_functions = {
        "eto_vs_temp": plot_eto_vs_temperature,
        "eto_vs_rad": plot_eto_vs_radiation,
        "temp_rad_prec": plot_temp_rad_prec,
        "heatmap": plot_heatmap,
        "correlation": plot_correlation
    }
    
    plot_function = plot_functions.get(graph_type)
    if plot_function:
        if graph_type == 'correlation':
            default_corr_var = df.columns.drop(['date', 'ETo'])[0]
            return plot_function(df, default_corr_var, lang=lang)
        return plot_function(df, lang=lang)
        
    return go.Figure()


# Callback 5: Renderiza o conteúdo da aba de Análise Estatística
@callback(
    Output("stats-container", "children"),
    Input("results-tabs", "active_tab"),
    State("eto-result-data", "data"),
    State('eto-language-store', 'data')
)
def render_stats_tab_content(active_tab, eto_data, lang):
    """Renderiza o conteúdo da aba de estatísticas quando ela é selecionada."""
    if active_tab != "tab-1" or not eto_data: return None
        
    t = get_translations_cached(lang)
    df = pd.DataFrame(eto_data)
    
    return html.Div([
        dbc.Row([
            dbc.Col(display_descriptive_stats(df, lang=lang), md=6),
            dbc.Col(display_normality_test(df, lang=lang), md=6),
        ], className="mb-4"),
        dbc.Row([dbc.Col(display_correlation_matrix(df, lang=lang))], className="mb-4"),
        dbc.Row([dbc.Col(display_eto_summary(df, lang=lang))])
    ])


# Callback 6: Lógica para download de dados
@callback(
    Output("download-csv", "data"),
    Output("download-excel", "data"),
    Input("download-csv-button", "n_clicks"),
    Input("download-excel-button", "n_clicks"),
    State("eto-result-data", "data"),
    State('eto-language-store', 'data'),
    prevent_initial_call=True
)
def download_data(csv_clicks, excel_clicks, eto_data, lang):
    """Gera e envia os arquivos de dados para download."""
    if not eto_data: return None, None

    t = get_translations_cached(lang)
    df = pd.DataFrame(eto_data)
    
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d/%m/%Y")
    df = df.round(2).rename(columns={
        "date": t["date"], "T2M_MAX": t["temp_max"], "T2M_MIN": t["temp_min"],
        "RH2M": t["humidity"], "WS2M": t["wind_speed"], "ALLSKY_SFC_SW_DWN": t["radiation"],
        "PRECTOTCORR": t["precipitation"], "ETo": t["eto"]
    })

    ctx = dash.callback_context
    if not ctx.triggered: return None, None
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "download-csv-button":
        return dcc.send_data_frame(df.to_csv, "eto_results.csv", index=False), None
    elif button_id == "download-excel-button":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="ETo Results")
        return None, dict(content=output.getvalue(), filename="eto_results.xlsx")
    
    return None, None

# --- INÍCIO DA SEÇÃO DE CALLBACKS ADICIONAIS ---

# Callback 7: Renderiza a UI de entrada de coordenadas (Global vs. MATOPIBA)
@callback(
    Output("coord-input-section", "children"),
    Input("calculation-mode", "value"),
    State('eto-language-store', 'data')
)
def render_coord_input_section(mode, lang):
    """Renderiza a interface correta para selecionar a localização."""
    t = get_translations_cached(lang)
    if mode == "Global":
        return html.Div([
            dbc.RadioItems(
                id="coord-option-global",
                options=[
                    {"label": t["click_to_select"], "value": "click"},
                    {"label": t["adjust_manually"], "value": "manual"}
                ],
                value="click",
            ),
            # Mapa ou inputs manuais serão renderizados aqui por outro callback
            html.Div(id="coord-input-dynamic-global")
        ])
    else: # MATOPIBA
        df, _ = load_matopiba_data(lang)
        states = sorted(df["UF"].unique()) if not df.empty else []
        return html.Div([
            dcc.Dropdown(id="matopiba-state", options=states, placeholder=t["choose_state"]),
            dcc.Dropdown(id="matopiba-city", placeholder=t["choose_city"], className="mt-2")
        ])

# Callback 8: Renderiza dinamicamente o mapa ou os inputs manuais para o modo Global
@callback(
    Output("coord-input-dynamic-global", "children"),
    Input("coord-option-global", "value"),
    State('eto-language-store', 'data')
)
def render_global_coord_input(option, lang):
    t = get_translations_cached(lang)
    if option == 'click':
        return dcc.Graph(
            id='global-map',
            figure=create_interactive_map(t), # Sua função que cria o mapa
            style={'height': '400px'}
        )
    else: # manual
        return dbc.Row([
            dbc.Col(dbc.Input(id="manual-lat", type="number", placeholder=t["latitude"])),
            dbc.Col(dbc.Input(id="manual-lng", type="number", placeholder=t["longitude"])),
        ], className="mt-2")


# Callback 9: Atualiza o dropdown de cidades quando um estado é selecionado
@callback(
    Output("matopiba-city", "options"),
    Output("matopiba-city", "value"),
    Input("matopiba-state", "value"),
    State('eto-language-store', 'data')
)
def update_city_dropdown(state, lang):
    """Filtra as cidades com base no estado selecionado no modo MATOPIBA."""
    if not state:
        return [], None
    df, _ = load_matopiba_data(lang)
    cities = sorted(df[df["UF"] == state]["CITY"].unique())
    return [{"label": city, "value": city} for city in cities], None


# Callback 10: Callback central para atualizar as coordenadas selecionadas
@callback(
    Output('eto-selected-coordinates', 'data', allow_duplicate=True),
    Input('global-map', 'clickData'),
    Input('manual-lat', 'value'),
    Input('manual-lng', 'value'),
    Input('matopiba-city', 'value'),
    State('calculation-mode', 'value'),
    State("matopiba-state", "value"),
    prevent_initial_call=True
)
def update_selected_coordinates(
    click_data: dict,
    manual_lat: float,
    manual_lng: float,
    city: str,
    mode: str,
    state: str
) -> dict:
    """
    Atualiza as coordenadas com base na interação do usuário.
    
    Args:
        click_data: Dados do clique no mapa
        manual_lat: Latitude inserida manualmente
        manual_lng: Longitude inserida manualmente
        city: Cidade selecionada (modo MATOPIBA)
        mode: Modo de cálculo
        state: Estado selecionado (modo MATOPIBA)
        
    Returns:
        dict: Coordenadas atualizadas ou no_update
    """
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    coords = None
    try:
        if triggered_id == 'global-map' and click_data:
            # Extrai coordenadas do clique no mapa
            point = click_data['points'][0]
            lat, lng = point['lat'], point['lon']
            coords = get_coordinates_with_elevation(lat, lng)

        elif triggered_id in ['manual-lat', 'manual-lng']:
            if manual_lat is not None and manual_lng is not None:
                # Valida e busca elevação para coordenadas manuais
                coords = get_coordinates_with_elevation(
                    manual_lat,
                    manual_lng
                )

        elif triggered_id == 'matopiba-city' and city and state:
            # Carrega dados do MATOPIBA
            df, _ = load_matopiba_data()
            city_data = df[
                (df["UF"] == state) & (df["CITY"] == city)
            ].iloc[0]
            
            coords = {
                'lat': city_data['LATITUDE'],
                'lng': city_data['LONGITUDE'],
                'elev': city_data['HEIGHT']
            }

        if coords:
            # Valida coordenadas antes de retornar
            is_valid, error_msg = EToState.validate_coordinates(coords)
            if is_valid:
                logger.info(f"Coordenadas atualizadas: {coords}")
                return coords
            else:
                logger.error(f"Coordenadas inválidas: {error_msg}")
                
    except Exception as e:
        logger.error(f"Erro ao atualizar coordenadas: {str(e)}")
    
    return no_update


def get_coordinates_with_elevation(lat: float, lng: float) -> Optional[dict]:
    """
    Busca elevação para um par de coordenadas.
    
    Args:
        lat: Latitude
        lng: Longitude
        
    Returns:
        dict: Coordenadas com elevação ou None se houver erro
    """
    try:
        response = call_api_with_retry(
            "/api/get_elevation",
            params={"lat": lat, "lng": lng}
        )
        elev = response.json().get("data", {}).get("elevation")
        
        if elev is not None:
            return {'lat': lat, 'lng': lng, 'elev': elev}
            
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar elevação: {str(e)}")
        
    return None


# Callback 11: Exibe os parâmetros selecionados para o usuário confirmar
@callback(
    Output('params-display', 'children'),
    Input('eto-selected-coordinates', 'data'),
    Input('data-source', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    State('eto-language-store', 'data')
)
def display_selected_parameters(coords, source, start_date, end_date, lang):
    """Mostra um resumo dos parâmetros selecionados antes do cálculo."""
    t = get_translations_cached(lang)
    if not coords:
        return t["select_location_prompt"]
    
    lines = [
        f"Lat: {coords.get('lat', 0):.4f}, Lng: {coords.get('lng', 0):.4f}, Elev: {coords.get('elev', 0):.0f}m",
        f"{t['database']}: {source or '...'}",
        f"{t['period']}: {start_date} a {end_date}"
    ]
    return [html.P(line, className="mb-0") for line in lines]


# Callback 12: Habilita/desabilita o botão de cálculo
@callback(
    Output('calculate-eto-button', 'disabled'),
    Input('eto-selected-coordinates', 'data'),
    Input('data-source', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
)
def toggle_calculate_button(coords, source, start_date, end_date):
    """Habilita o botão de cálculo apenas quando todos os parâmetros são válidos."""
    return not all([coords, source, start_date, end_date])

# --- FIM DA SEÇÃO DE CALLBACKS ADICIONAIS ---
