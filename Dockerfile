FROM python:3.10-slim

WORKDIR /app

# Copia arquivos necessários
COPY requirements.txt .
COPY setup.sh .
COPY api/ ./api/
COPY src/ ./src/
COPY pages/ ./pages/
COPY assets/ ./assets/
COPY utils/ ./utils/
COPY components/ ./components/

# Torna o setup.sh executável
RUN chmod +x setup.sh

# Executa o setup.sh para configurar localidade e instalar dependências
RUN ./setup.sh

# Expõe portas para api e web
EXPOSE 8000 8050

# Comando padrão (será sobrescrito no docker-compose.yml)
CMD ["echo", "Define SERVICE and CMD in docker-compose.yml"]