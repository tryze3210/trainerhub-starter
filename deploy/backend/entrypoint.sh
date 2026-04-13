#!/bin/sh
set -e

cd /app/backend
python manage.py migrate --noinput || true
python manage.py collectstatic --noinput || true
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
