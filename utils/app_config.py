"""
Configuração e inicialização do aplicativo EVAOnline.

Este módulo contém funções para validar o ambiente, configurar 
o aplicativo Dash e inicializar componentes essenciais.
"""

import os
from typing import Dict

import dash
import dash_bootstrap_components as dbc
from dotenv import load_dotenv
from flask import Response
from loguru import logger
from prometheus_client import Counter, generate_latest

from utils.logging import configure_logging


def validate_environment() -> Dict[str, any]:
    """
    Valida e carrega as variáveis de ambiente necessárias.
    
    Returns:
        dict: Configurações validadas
    
    Raises:
        ValueError: Se alguma variável obrigatória estiver faltando
    """
    config = {
        'api_url': os.getenv('API_URL', 'http://api:8000'),
        'debug_mode': os.getenv('DEBUG', 'false').lower() == 'true',
        'app_port': int(os.getenv('APP_PORT', '8050')),
        'app_host': os.getenv('APP_HOST', '0.0.0.0')
    }
    
    # Valida a URL da API
    if not config['api_url'].startswith(('http://', 'https://')):
        raise ValueError(f"API_URL inválida: {config['api_url']}")
    
    return config


def create_app():
    """
    Cria e configura a instância do aplicativo Dash.
    
    Returns:
        tuple: (app, config) - A instância do aplicativo Dash e a configuração
    """
    # Carrega as variáveis de ambiente do arquivo .env
    load_dotenv()
    
    # Inicializa configurações
    try:
        config = validate_environment()
        configure_logging()
        logger.info("Configurações carregadas com sucesso")
    except ValueError as e:
        logger.critical(f"Erro nas configurações: {e}")
        raise
    
    # Inicializa a aplicação Dash com tema moderno
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.LUMEN,
            "/assets/styles.css"
        ],
        suppress_callback_exceptions=True,
        meta_tags=[{
            "name": "viewport",
            "content": "width=device-width, initial-scale=1"
        }]
    )
    
    # Configurações adicionais que são suportadas via app.config
    app.config.update({
        'suppress_callback_exceptions': True
    })
    
    # Retorna a instância do aplicativo e a configuração
    return app, config


def register_metrics(app):
    """
    Registra métricas do Prometheus e rotas relacionadas.
    
    Args:
        app: A instância do aplicativo Dash
    
    Returns:
        tuple: (REQUESTS_DASH, MAP_INTERACTIONS, NAVIGATION_ETO)
    """
    # Métricas Prometheus
    REQUESTS_DASH = Counter(
        'evaonline_dash_requests_total', 
        'Total Dash Requests'
    )
    MAP_INTERACTIONS = Counter(
        'evaonline_map_interactions_total', 
        'Total Map Interactions'
    )
    NAVIGATION_ETO = Counter(
        'evaonline_navigation_eto_total', 
        'Total Navigations to ETo'
    )
    
    # Rota de métricas do Prometheus
    @app.server.route("/metrics")
    def metrics():
        REQUESTS_DASH.inc()
        return Response(generate_latest(), mimetype="text/plain")
    
    return REQUESTS_DASH, MAP_INTERACTIONS, NAVIGATION_ETO
