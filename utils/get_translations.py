import os
import json
from typing import Dict
from loguru import logger

# Cache em memória para armazenar as traduções já carregadas
_translations_cache = {}


def get_translations(lang: str = "pt") -> Dict[str, str]:
    """
    Carrega as traduções de um arquivo JSON correspondente ao idioma,
    com cache em memória para otimizar o desempenho.

    Esta função espera que exista uma pasta 'translations' na raiz do projeto
    contendo os arquivos, como 'translations/pt.json' e 'translations/en.json'.

    Args:
        lang (str): O código do idioma (ex: 'pt', 'en').

    Returns:
        Dict[str, str]: Um dicionário contendo os textos traduzidos.
    """
    # 1. Verifica se a tradução já está no cache para evitar ler o arquivo novamente
    if lang in _translations_cache:
        return _translations_cache[lang]

    # 2. Constrói o caminho para o arquivo JSON de forma dinâmica
    #    Isso funciona bem localmente e dentro do Docker.
    #    Certifique-se de que a pasta 'translations' está na raiz do seu projeto.
    file_path = os.path.join("translations", f"{lang}.json")
    
    try:
        # 3. Abre e carrega o arquivo JSON
        with open(file_path, "r", encoding="utf-8") as f:
            translations = json.load(f)
            _translations_cache[lang] = translations  # Armazena no cache para futuras chamadas
            logger.info(f"Traduções para '{lang}' carregadas do arquivo: {file_path}")
            return translations
            
    except FileNotFoundError:
        logger.warning(f"Arquivo de tradução não encontrado para '{lang}' em '{file_path}'. Usando 'pt' como fallback.")
        # 4. Se o arquivo do idioma solicitado não for encontrado, tenta carregar o português como padrão.
        if lang != "pt":
            return get_translations("pt")
        else:
            # Se nem o arquivo de português for encontrado, retorna um dicionário vazio para evitar que o app quebre.
            logger.error("Arquivo de tradução padrão 'pt.json' não encontrado. A interface pode aparecer sem textos.")
            return {}
            
    except json.JSONDecodeError:
        logger.error(f"Erro de sintaxe no arquivo JSON: {file_path}. Verifique se o JSON é válido.")
        return {} # Retorna vazio para não quebrar a aplicação