#!/bin/bash
set -e

echo "Waiting for database \"$DB_HOST:$DB_PORT\" to be ready..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done
echo "Database is ready."

if [ ! -f "/app/.app_initialized" ]; then
    echo "Initializing App..."

    echo "Running Database Migrations..."
    python manage.py migrate

    echo "Loading Permissions..."
    python manage.py load_permissions

    echo "Building Tailwind CSS..."
    make npm_install
    make build_client

    echo "Collecting static files..."
    python manage.py collectstatic --noinput

    touch /app/.app_initialized
    chmod 400 /app/.app_initialized
else
    echo "App already initialized, skipping..."
fi

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind "${GUNICORN_BIND:-0.0.0.0:8000}" \
    --workers "${GUNICORN_WORKERS:-4}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --log-level "${LOG_LEVEL:-WARNING}"
