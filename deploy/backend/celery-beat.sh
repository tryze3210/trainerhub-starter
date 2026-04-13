#!/bin/sh
set -e

cd /app/backend
exec celery -A config.celery_app beat --loglevel=INFO
