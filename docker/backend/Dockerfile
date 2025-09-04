FROM python:3.10-slim

LABEL maintainer="Ângela Cunha Soares <angelassilviane@gmail.com>"

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    TZ=America/Sao_Paulo

# Copiar requirements primeiro para aproveitar cache do Docker
COPY requirements/base.txt requirements/prod.txt ./

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r prod.txt

# Copiar código da aplicação
COPY backend/ /app/backend/
COPY config/ /app/config/
COPY docker/backend/entrypoint.sh /app/

# Tornar entrypoint executável
RUN chmod +x /app/entrypoint.sh

# Criar usuário não-root
RUN useradd -m -u 1000 evaonline && \
    chown -R evaonline:evaonline /app

# Mudar para usuário não-root
USER evaonline

# Expor porta
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
