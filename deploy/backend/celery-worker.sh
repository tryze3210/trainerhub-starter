#!/bin/sh
set -e

cd /app/backend
exec celery -A config.celery_app worker --loglevel=INFO --queues=default,media,notifications,billing
