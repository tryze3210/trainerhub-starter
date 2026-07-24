#!/bin/sh
set -e

cd /app/backend
exec celery -A config.celery_app worker --loglevel=INFO --queues="${CELERY_WORKER_QUEUES:-default,outbox,ops,email,media,notifications,billing}"
