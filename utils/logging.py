from loguru import logger
import sys
import os


def configure_logging(log_file: str = "logs/app.log", level: str = "INFO"):
    """
    Configura o logging com Loguru para a aplicação EVAonline.

    Parâmetros:
    - log_file: Caminho para o arquivo de log (padrão: logs/app.log)
    - level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Criar diretório de logs, se não existir
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Remover o handler padrão do Loguru (console) para evitar duplicação
    logger.remove()

    # Configurar logging para o console
    logger.add(
        sys.stdout,
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"
    )

    # Configurar logging para arquivo com rotação (máximo 10 MB por arquivo)
    logger.add(
        log_file,
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
        rotation="10 MB",  # Rotaciona o arquivo quando atingir 10 MB
        retention="7 days",  # Mantém logs por 7 dias
        compression="zip"  # Comprime logs antigos
    )

    logger.info("Logging configurado com sucesso")


# Configurar logging na inicialização
configure_logging()