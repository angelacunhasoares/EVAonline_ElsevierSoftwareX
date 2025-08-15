FROM python:3.10-slim

WORKDIR /app

COPY requirements-celery.txt .
COPY setup.sh .
COPY src/ ./src/
COPY data/ ./data/

RUN chmod +x setup.sh
ENV SERVICE=src
RUN ./setup.sh

CMD ["python", "src/data_download.py"]  # Ajuste conforme o script principal