from pathlib import Path
from loguru import logger

def get_static_resource_path(resource_name: str) -> str:
    """
    Retorna o caminho relativo para um recurso estático na pasta assets/.

    Parâmetros:
    - resource_name: Nome do arquivo (ex.: 'home_gif.gif', 'styles.css').

    Retorna:
    - Caminho relativo para uso no Dash (ex.: '/assets/home_gif.gif').
    """
    try:
        asset_path = Path("assets") / resource_name
        if not asset_path.exists():
            logger.error(f"Recurso estático não encontrado: {asset_path}")
            raise FileNotFoundError(f"Recurso estático não encontrado: {asset_path}")
        logger.info(f"Recurso estático carregado: {asset_path}")
        return f"/assets/{resource_name}"
    except Exception as e:
        logger.error(f"Erro ao carregar recurso estático: {str(e)}")
        raise