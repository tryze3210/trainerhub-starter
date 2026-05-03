from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.getenv('DJANGO_SETTINGS_MODULE', 'config.settings.local'))

app = Celery('trainerhub')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


OUTBOX_QUEUE = os.getenv('CELERY_OUTBOX_QUEUE', 'outbox')
DEFAULT_QUEUE = os.getenv('CELERY_TASK_DEFAULT_QUEUE', 'default')

# Keep event processing isolated from regular background work. A burst of media
# jobs must not starve payment/order/entitlement projections.
app.conf.task_default_queue = DEFAULT_QUEUE
app.conf.task_routes = {
    'apps.events.tasks.dispatch_pending_outbox_task': {'queue': OUTBOX_QUEUE},
    'apps.events.tasks.requeue_stuck_outbox_task': {'queue': OUTBOX_QUEUE},
    'apps.events.tasks.outbox_healthcheck_task': {'queue': OUTBOX_QUEUE},
}

# Celery Beat schedule. The task bodies are bounded, so running them often is
# safe: each invocation claims a small batch and exits.
app.conf.beat_schedule = {
    'trainerhub-events-dispatch-outbox': {
        'task': 'apps.events.tasks.dispatch_pending_outbox_task',
        'schedule': _float_env('CELERY_OUTBOX_DISPATCH_EVERY_SECONDS', 5.0),
        'kwargs': {
            'batch_size': _int_env('CELERY_OUTBOX_DISPATCH_BATCH_SIZE', 100),
            'max_batches': _int_env('CELERY_OUTBOX_DISPATCH_MAX_BATCHES', 5),
        },
        'options': {'queue': OUTBOX_QUEUE},
    },
    'trainerhub-events-requeue-stuck-outbox': {
        'task': 'apps.events.tasks.requeue_stuck_outbox_task',
        'schedule': _float_env('CELERY_OUTBOX_REQUEUE_EVERY_SECONDS', 60.0),
        'kwargs': {
            'older_than_minutes': _int_env('CELERY_OUTBOX_REQUEUE_OLDER_THAN_MINUTES', 15),
            'limit': _int_env('CELERY_OUTBOX_REQUEUE_LIMIT', 100),
        },
        'options': {'queue': OUTBOX_QUEUE},
    },
    'trainerhub-events-outbox-healthcheck': {
        'task': 'apps.events.tasks.outbox_healthcheck_task',
        'schedule': _float_env('CELERY_OUTBOX_HEALTH_EVERY_SECONDS', 60.0),
        'kwargs': {'fail_on_unhealthy': False},
        'options': {'queue': OUTBOX_QUEUE},
    },
}


@app.task(bind=True, name='trainerhub.debug_task')
def debug_task(self):
    return {'task_id': self.request.id, 'name': self.name}
