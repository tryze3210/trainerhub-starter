# TrainerHub Events Outbox Worker

The commercial lifecycle emits persistent `DomainEvent` rows and `OutboxMessage` rows. These messages are processed by Celery tasks so payment, entitlement, analytics, notification and payout projections are not coupled directly to HTTP requests.

## Local one-shot dispatch

```bash
cd backend
source .venv/bin/activate
python manage.py dispatch_outbox --batch-size 100 --max-batches 10 --json
```

## Celery worker

```bash
cd backend
celery -A config.celery worker --loglevel=INFO --queues=outbox,default --concurrency=2
```

## Celery Beat

```bash
cd backend
celery -A config.celery beat --loglevel=INFO
```

Beat schedules three bounded tasks:

- `apps.events.tasks.dispatch_pending_outbox_task`
- `apps.events.tasks.requeue_stuck_outbox_task`
- `apps.events.tasks.outbox_healthcheck_task`

## Docker overlay

```bash
docker compose -f docker-compose.yml -f docker-compose.outbox.yml up -d celery-outbox-worker celery-beat
```

The overlay expects your base compose file to define healthy `postgres` and `redis` services.

## Useful env vars

```env
CELERY_OUTBOX_QUEUE=outbox
CELERY_OUTBOX_WORKER_CONCURRENCY=2
CELERY_OUTBOX_DISPATCH_EVERY_SECONDS=5
CELERY_OUTBOX_DISPATCH_BATCH_SIZE=100
CELERY_OUTBOX_DISPATCH_MAX_BATCHES=5
CELERY_OUTBOX_REQUEUE_EVERY_SECONDS=60
CELERY_OUTBOX_REQUEUE_OLDER_THAN_MINUTES=15
CELERY_OUTBOX_REQUEUE_LIMIT=100
CELERY_OUTBOX_HEALTH_EVERY_SECONDS=60
```

## Healthcheck

```bash
python manage.py outbox_health --json --fail-on-unhealthy
```

HTTP admin endpoint:

```http
GET /api/v1/events/outbox/health/
```
