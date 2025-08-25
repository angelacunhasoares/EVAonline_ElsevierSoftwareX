FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements/base.txt .
COPY requirements/prod.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r prod.txt

# Copy application code
COPY backend /app/backend
COPY docker/backend/entrypoint.sh /app/

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
