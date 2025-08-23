"""
Serviço de tradução com cache para o aplicativo EVAOnline.

Este módulo fornece funções para recuperar traduções da API ou arquivos locais,
com implementação de cache para melhorar o desempenho.
"""

import requests
from loguru import logger

from utils.get_translations import get_translations as get_translations_local

# Cache para armazenar traduções
_translations_cache = {}

def get_translations_cached(api_url: str, lang: str = "en") -> dict:
    """
    Busca traduções da API com cache e fallback para arquivo local.
    
    Args:
        api_url (str): URL base da API
        lang (str): Código do idioma (pt/en)
    
    Returns:
        dict: Dicionário com as traduções
    
    Note:
        Usa cache em memória para reduzir chamadas à API.
        Em caso de falha na API, utiliza arquivo local como fallback.
    """
    # Verifica se já está em cache
    if lang in _translations_cache:
        return _translations_cache[lang]
    
    try:
        # Tenta buscar da API com timeout
        response = requests.get(
            f"{api_url}/api/translations/{lang}",
            timeout=5.0  # 5 segundos de timeout
        )
        response.raise_for_status()
        translations = response.json()
        
        # Armazena no cache
        _translations_cache[lang] = translations
        
        logger.info(f"Traduções carregadas da API para o idioma '{lang}'")
        return translations
        
    except requests.Timeout:
        logger.error(f"Timeout ao buscar traduções da API para '{lang}'")
        return get_translations_local(lang)
        
    except requests.RequestException as e:
        logger.error(
            f"Erro ao buscar traduções da API para '{lang}'. "
            f"Usando fallback local. Erro: {str(e)}"
        )
        return get_translations_local(lang)
