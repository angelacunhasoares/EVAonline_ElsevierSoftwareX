"""
Callbacks para componente de seleção de fontes climáticas.
Implementa proteções de conformidade Open-Meteo (CC-BY-NC 4.0).
"""

from typing import List

from dash import Input, Output, State, callback, html
from dash.exceptions import PreventUpdate


@callback(
    Output("openmeteo-fusion-warning", "style"),
    Output("download-data-btn", "disabled"),
    Output("download-data-btn", "title"),
    Input("data-fusion-mode", "value"),
    Input({"type": "source-checkbox", "source": "openmeteo"}, "value"),
    prevent_initial_call=True
)
def handle_openmeteo_restrictions(
    fusion_mode: str,
    openmeteo_checked: bool
) -> tuple:
    """
    Gerencia restrições de Open-Meteo (CC-BY-NC 4.0):
    - Mostra warning se Open-Meteo selecionado em modo fusão
    - Desabilita download se Open-Meteo selecionado
    
    Args:
        fusion_mode: 'fusion' ou 'single'
        openmeteo_checked: Se Open-Meteo está selecionado
        
    Returns:
        tuple: (warning_style, download_disabled, download_tooltip)
    """
    # Warning visível se Open-Meteo em modo fusão
    show_warning = fusion_mode == "fusion" and openmeteo_checked
    warning_style = {"display": "block"} if show_warning else {"display": "none"}
    
    # Download desabilitado se Open-Meteo selecionado (qualquer modo)
    download_disabled = openmeteo_checked
    download_tooltip = (
        "Download não disponível para Open-Meteo (CC-BY-NC 4.0). "
        "Dados restritos a visualização apenas."
        if openmeteo_checked
        else "Baixar dados climáticos processados"
    )
    
    return warning_style, download_disabled, download_tooltip


@callback(
    Output("single-source-selector", "style"),
    Input("data-fusion-mode", "value"),
    prevent_initial_call=True
)
def toggle_single_source_dropdown(mode: str) -> dict:
    """
    Mostra/esconde dropdown de fonte única baseado no modo selecionado.
    
    Args:
        mode: 'fusion' ou 'single'
        
    Returns:
        dict: Estilo CSS (display: block/none)
    """
    if mode == "single":
        return {"display": "block"}
    return {"display": "none"}


@callback(
    Output("fusion-weights-info", "children"),
    Input("data-fusion-mode", "value"),
    State({"type": "source-checkbox", "source": "openmeteo"}, "value"),
    State({"type": "source-checkbox", "source": "nasa_power"}, "value"),
    State({"type": "source-checkbox", "source": "met_norway"}, "value"),
    State({"type": "source-checkbox", "source": "nws_usa"}, "value"),
    prevent_initial_call=True
)
def update_fusion_info(
    mode: str,
    openmeteo: bool,
    nasa_power: bool,
    met_norway: bool,
    nws_usa: bool
) -> html.Div:
    """
    Atualiza informações sobre fontes selecionadas para fusão.
    Valida que Open-Meteo não está incluído.
    
    Args:
        mode: 'fusion' ou 'single'
        openmeteo: Se Open-Meteo está selecionado
        nasa_power: Se NASA POWER está selecionado
        met_norway: Se MET Norway está selecionado
        nws_usa: Se NWS está selecionado
        
    Returns:
        html.Div: Informações sobre fontes para fusão
    """
    if mode != "fusion":
        raise PreventUpdate
    
    # Coletar fontes selecionadas (exceto Open-Meteo)
    fusion_sources = []
    if nasa_power:
        fusion_sources.append("NASA POWER")
    if met_norway:
        fusion_sources.append("MET Norway")
    if nws_usa:
        fusion_sources.append("NWS")
    
    if not fusion_sources:
        return html.Div([
            html.I(className="bi bi-exclamation-circle me-2"),
            "⚠️ Selecione pelo menos uma fonte para fusão de dados."
        ], className="text-warning")
    
    if openmeteo and len(fusion_sources) == 0:
        return html.Div([
            html.I(className="bi bi-x-circle me-2"),
            "❌ Open-Meteo não pode ser usado sozinho em fusão. "
            "Selecione outras fontes ou use 'Fonte Única'."
        ], className="text-danger")
    
    return html.Div([
        html.I(className="bi bi-check-circle me-2"),
        f"✅ Fusão ativa com {len(fusion_sources)} fonte(s): ",
        html.Strong(", ".join(fusion_sources))
    ], className="text-success")


@callback(
    Output("data-download-format", "options"),
    Output("data-download-format", "value"),
    Input("single-source-dropdown", "value"),
    Input({"type": "source-checkbox", "source": "openmeteo"}, "value"),
    prevent_initial_call=True
)
def update_download_formats(
    selected_source: str,
    openmeteo_checked: bool
) -> tuple:
    """
    Atualiza formatos de download disponíveis.
    Remove opções se Open-Meteo selecionado.
    
    Args:
        selected_source: Fonte selecionada no modo single
        openmeteo_checked: Se Open-Meteo está marcado
        
    Returns:
        tuple: (options, default_value)
    """
    if openmeteo_checked:
        # Nenhum formato disponível para Open-Meteo
        return [], None
    
    # Formatos padrão para outras fontes
    formats = [
        {"label": "CSV (Excel compatível)", "value": "csv"},
        {"label": "JSON (API format)", "value": "json"},
        {"label": "NetCDF (científico)", "value": "nc"}
    ]
    
    return formats, "csv"


@callback(
    Output("attribution-footer", "children"),
    Input({"type": "source-checkbox", "source": "openmeteo"}, "value"),
    Input({"type": "source-checkbox", "source": "nasa_power"}, "value"),
    Input({"type": "source-checkbox", "source": "met_norway"}, "value"),
    Input({"type": "source-checkbox", "source": "nws_usa"}, "value"),
    prevent_initial_call=True
)
def update_attribution(
    openmeteo: bool,
    nasa_power: bool,
    met_norway: bool,
    nws_usa: bool
) -> html.Div:
    """
    Atualiza footer com atribuições necessárias baseado em fontes selecionadas.
    
    Args:
        openmeteo: Se Open-Meteo está selecionado
        nasa_power: Se NASA POWER está selecionado
        met_norway: Se MET Norway está selecionado
        nws_usa: Se NWS está selecionado
        
    Returns:
        html.Div: Footer com atribuições
    """
    attributions = []
    
    if openmeteo:
        attributions.append(
            html.Div([
                "Weather data: ",
                html.A(
                    "Open-Meteo.com",
                    href="https://open-meteo.com",
                    target="_blank",
                    className="text-decoration-none"
                ),
                " (CC-BY-NC 4.0)"
            ])
        )
    
    if nasa_power:
        attributions.append(
            html.Div([
                "Data source: ",
                html.A(
                    "NASA POWER",
                    href="https://power.larc.nasa.gov",
                    target="_blank",
                    className="text-decoration-none"
                ),
                " (Public Domain)"
            ])
        )
    
    if met_norway:
        attributions.append(
            html.Div([
                "Data source: ",
                html.A(
                    "MET Norway",
                    href="https://api.met.no",
                    target="_blank",
                    className="text-decoration-none"
                ),
                " (CC-BY 4.0)"
            ])
        )
    
    if nws_usa:
        attributions.append(
            html.Div([
                "Data source: ",
                html.A(
                    "NOAA National Weather Service",
                    href="https://www.weather.gov",
                    target="_blank",
                    className="text-decoration-none"
                ),
                " (US Public Domain)"
            ])
        )
    
    if not attributions:
        raise PreventUpdate
    
    return html.Div(
        attributions,
        className="text-muted small mt-3"
    )


@callback(
    Output("available-sources-store", "data"),
    Input("selected-location-store", "data"),
    prevent_initial_call=True
)
def detect_available_sources(location_data: dict) -> dict:
    """
    Detecta fontes de dados climáticos disponíveis para a localização
    selecionada no mapa mundial.
    
    Utiliza ClimateSourceManager.get_available_sources_for_location()
    que automaticamente:
    - Verifica cobertura geográfica (bbox intersection)
    - Exclui Open-Meteo (CC-BY-NC 4.0, MATOPIBA only)
    - Retorna apenas fontes disponíveis para fusão
    
    Args:
        location_data: {"lat": float, "lon": float, "name": str}
        
    Returns:
        dict: Fontes disponíveis com metadados
            {
                "nasa_power": {
                    "available": True,
                    "name": "NASA POWER",
                    "bbox_str": "Global coverage",
                    ...
                },
                ...
            }
    
    Example:
        >>> # Usuário clica em Paris (48.8566°N, 2.3522°E)
        >>> detect_available_sources({
        ...     "lat": 48.8566,
        ...     "lon": 2.3522,
        ...     "name": "Paris"
        ... })
        >>> # Retorna: nasa_power (global) + met_norway (Europa)
        >>> # Exclui: openmeteo (non-commercial), nws_usa (fora bbox)
    """
    if not location_data:
        raise PreventUpdate
    
    lat = location_data.get("lat")
    lon = location_data.get("lon")
    
    if lat is None or lon is None:
        raise PreventUpdate
    
    # Import necessário (evitar circular imports)
    try:
        from backend.api.services.climate_source_manager import \
            ClimateSourceManager
    except ImportError:
        # Fallback se backend não disponível
        return {}
    
    # Inicializar gerenciador e detectar fontes
    manager = ClimateSourceManager()
    sources = manager.get_available_sources_for_location(
        lat=lat,
        lon=lon,
        exclude_non_commercial=True  # Exclui Open-Meteo para mundial
    )
    
    return sources


@callback(
    Output("climate-sources-card", "children"),
    Input("available-sources-store", "data"),
    prevent_initial_call=True
)
def render_climate_source_selector(sources_data: dict):
    """
    Renderiza o seletor de fontes de dados climáticos baseado
    nas fontes disponíveis para a localização selecionada.
    
    Args:
        sources_data: Dicionário de fontes disponíveis do store
            (retornado por detect_available_sources)
    
    Returns:
        Component: Card com seletor de fontes ou mensagem de
                  seleção de localização
    
    Example:
        >>> # Após usuário clicar em Paris
        >>> sources_data = {
        ...     "nasa_power": {"available": True, ...},
        ...     "met_norway": {"available": True, ...}
        ... }
        >>> # Renderiza card com 2 checkboxes (NASA + MET)
    """
    if not sources_data:
        # Mensagem inicial: nenhuma localização selecionada
        return html.Div([
            html.I(
                className="bi bi-info-circle text-muted",
                style={"fontSize": "2rem"}
            ),
            html.P(
                "Selecione uma localização no mapa mundial para "
                "visualizar as fontes de dados climáticos disponíveis.",
                className="text-muted text-center mt-3"
            )
        ], className="text-center py-5")
    
    # Converter dict para list (formato esperado pelo selector)
    available_sources = []
    for source_id, metadata in sources_data.items():
        if metadata.get("available", False):
            available_sources.append({
                "id": source_id,
                "name": metadata["name"],
                "coverage": metadata["coverage"],
                "bbox_str": metadata["bbox_str"],
                "license": metadata["license"],
                "can_fuse": metadata["can_fuse"],
                "can_download": metadata["can_download"],
                "realtime": metadata["realtime"],
                "temporal": metadata["temporal"],
                "available": True,
                "attribution_required": metadata.get(
                    "attribution_required", False
                )
            })
    
    # Import do componente
    from frontend.components.climate_source_selector import \
        create_climate_source_selector

    # Renderizar seletor
    return create_climate_source_selector(available_sources)
