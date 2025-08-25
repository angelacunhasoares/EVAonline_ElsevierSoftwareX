"""
EVAonline About Page

Este módulo implementa a página 'Sobre' do EVAonline, que fornece:
- Descrição geral do sistema
- Explicação do modelo de evapotranspiração
- Recursos e funcionalidades
- Links úteis e documentação
- Informações de contato e citação
"""

# Standard library imports
from typing import Dict

# Third-party imports
import dash_bootstrap_components as dbc
from dash import html, dcc
from loguru import logger

# Local imports
from utils.get_translations import get_translations
from config.api_config import API_CONFIG, call_api_with_retry

# Cache de traduções
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
        response = call_api_with_retry("/api/translations/" + lang)
        translations = response.json()
        
        # Armazena no cache
        _translations_cache[lang] = translations
        logger.info(f"Traduções carregadas da API para '{lang}'")
        
        return translations
        
    except Exception as e:
        logger.error(
            f"Erro ao buscar traduções para '{lang}'. "
            f"Usando fallback local. Erro: {str(e)}"
        )
        return get_translations(lang)

def create_eto_explanation(t: dict) -> html.Div:
    """
    Cria a seção de explicação da fórmula de ETo.
    
    Args:
        t: Dicionário de traduções
        
    Returns:
        html.Div: Componente com a explicação
    """
    return html.Div([
        html.H2(t["what_is_evaonline_title"], className="h4 mb-3"),
        html.P(t["what_is_evaonline_desc"], className="text-justify"),
        
        # Fórmula LaTeX com MathJax
        html.Div([
            dcc.Markdown(
                r"""
                $$ET_0 = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}
                {T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$
                """,
                mathjax=True
            )
        ], style={"overflowX": "auto", "textAlign": "center"}),
        
        html.P(
            t["what_is_evaonline_desc_explanation"],
            className="text-justify mt-3"
        )
    ])


def create_features_section(t: dict) -> dbc.Accordion:
    """
    Cria a seção de recursos e funcionalidades.
    
    Args:
        t: Dicionário de traduções
        
    Returns:
        dbc.Accordion: Componente com os recursos
    """
    return dbc.Accordion([
        dbc.AccordionItem(
            title=t["why_use_evaonline_title"],
            children=[
                html.P(t["why_use_evaonline_desc"], className="text-justify")
            ]
        ),
        dbc.AccordionItem(
            title=t["features_title"],
            children=[
                html.P(t["features_desc"], className="text-justify")
            ]
        ),
        dbc.AccordionItem(
            title=t["citation_title"],
            children=[
                html.P(t["citation_text"], className="text-justify"),
                html.Pre(
                    t["citation_format"],
                    className="bg-light p-3 rounded"
                )
            ]
        )
    ], start_collapsed=True, className="mt-3")


def create_contact_section(t: dict) -> dbc.Card:
    """
    Cria a seção de contato e links úteis.
    
    Args:
        t: Dicionário de traduções
        
    Returns:
        dbc.Card: Componente com informações de contato
    """
    return dbc.Card(
        dbc.CardBody([
            html.H3(t["contact_title"], className="h5 mb-3"),
            html.P(t["contact_text"]),
            dbc.Row([
                dbc.Col(
                    dbc.Button(
                        [html.I(className="fas fa-home me-2"), "Home"],
                        href="/",
                        color="primary",
                        className="w-100"
                    ),
                    width=6
                ),
                dbc.Col(
                    dbc.Button(
                        [html.I(className="fas fa-book me-2"), "Docs"],
                        href="https://github.com/angelacunhasoares/"
                             "EVAonline_ElsevierSoftwareX",
                        color="secondary",
                        className="w-100",
                        target="_blank"
                    ),
                    width=6
                )
            ])
        ]),
        className="mt-4"
    )


def layout(lang: str = "pt") -> dbc.Container:
    """
    Cria o layout completo da página 'Sobre'.
    
    Args:
        lang: Código do idioma (pt/en)
        
    Returns:
        dbc.Container: Layout completo da página
    """
    t = get_translations_cached(lang)
    
    return dbc.Container([
        # Conteúdo principal
        dbc.Card(
            dbc.CardBody([
                html.H1(t["about_title"], className="display-4 mb-4"),
                create_eto_explanation(t),
                create_features_section(t)
            ]),
            className="mt-4"
        ),
        
        # Seção de contato e links
        create_contact_section(t)
    ], fluid=True)

# --- FIM DAS MUDANÇAS ---
