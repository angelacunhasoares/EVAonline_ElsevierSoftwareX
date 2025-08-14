from dash import callback_context
from loguru import logger

def reset_state(stores: list[str]):
    """
    Reseta os dados armazenados nos componentes dcc.Store especificados.

    Parâmetros:
    - stores: Lista de IDs dos componentes dcc.Store a serem resetados.
    """
    try:
        ctx = callback_context
        if not ctx.triggered:
            return

        for store_id in stores:
            ctx.outputs_list[store_id] = None  # Limpa o estado no dcc.Store
        logger.info("Estado resetado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao resetar estado: {str(e)}")