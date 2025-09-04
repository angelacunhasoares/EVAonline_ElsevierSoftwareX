FROM python:3.10-slim

LABEL maintainer="Ângela Cunha Soares <angelassilviane@gmail.com>"

# Instalar dependências do sistema
RUN apt-get update && \
    apt-get install -y \
    locales \
    build-essential \
    curl \
    dos2unix \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    REDIS_URL=redis://redis:6379/0 \
    CELERY_BROKER_URL=redis://redis:6379/0 \
    CELERY_RESULT_BACKEND=redis://redis:6379/0 \
    TZ=America/Sao_Paulo \
    SERVICE=all

# Copiar requirements primeiro para aproveitar cache do Docker
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn uvicorn[standard] prometheus_client pytest

# Configurar localidade
RUN echo "pt_BR.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen pt_BR.UTF-8 && \
    update-locale LANG=pt_BR.UTF-8

# Copiar script de entrada
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && \
    dos2unix /usr/local/bin/entrypoint.sh

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários e configurar permissões
RUN mkdir -p /app/logs /app/data /app/temp && \
    chmod -R 755 /app/logs /app/data /app/temp && \
    useradd -m -u 1000 evaonline && \
    chown -R evaonline:evaonline /app

# Mudar para usuário não-root
USER evaonline

# Expor portas
EXPOSE 8000 8050

# Healthcheck melhorado
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || curl -f http://localhost:8050/ || exit 1

# Comando padrão
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
