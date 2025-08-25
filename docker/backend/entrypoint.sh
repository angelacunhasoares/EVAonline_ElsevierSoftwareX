#!/bin/sh

# Wait for services to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
    sleep 1
done

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
    sleep 1
done

# Run database migrations
alembic upgrade head

# Start the FastAPI application
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
