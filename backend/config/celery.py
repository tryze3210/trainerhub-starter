from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    os.getenv('DJANGO_SETTINGS_MODULE', 'config.settings.local'),
)

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
OPS_QUEUE = os.getenv('CELERY_OPS_QUEUE', 'ops')
DEFAULT_QUEUE = os.getenv('CELERY_TASK_DEFAULT_QUEUE', 'default')

# Keep event processing isolated from regular background work. A burst of media
# jobs must not starve payment/order/entitlement projections.
app.conf.task_default_queue = DEFAULT_QUEUE
app.conf.task_routes = {
    'apps.events.tasks.dispatch_pending_outbox_task': {'queue': OUTBOX_QUEUE},
    'apps.events.tasks.requeue_stuck_outbox_task': {'queue': OUTBOX_QUEUE},
    'apps.events.tasks.outbox_healthcheck_task': {'queue': OUTBOX_QUEUE},
    'apps.ops.tasks.capture_reconciliation_snapshot_task': {'queue': OPS_QUEUE},
    'apps.ops.tasks.prune_reconciliation_snapshots_task': {'queue': OPS_QUEUE},
}

# Celery Beat schedule. The task bodies are bounded, so running them often is
# safe: each invocation claims a small batch or writes one compact ops snapshot.
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
    'trainerhub-ops-reconciliation-snapshot-capture': {
        'task': 'apps.ops.tasks.capture_reconciliation_snapshot_task',
        'schedule': _float_env('CELERY_RECONCILIATION_SNAPSHOT_EVERY_SECONDS', 3600.0),
        'kwargs': {
            'limit': _int_env('CELERY_RECONCILIATION_SNAPSHOT_LIMIT', 100),
            'source': os.getenv('CELERY_RECONCILIATION_SNAPSHOT_SOURCE', 'scheduled'),
            'min_age_minutes': _int_env('CELERY_RECONCILIATION_SNAPSHOT_MIN_AGE_MINUTES', 60),
            'force': False,
            'emit_alerts': os.getenv('CELERY_RECONCILIATION_SNAPSHOT_ALERTS_ENABLED', 'true').lower() in {'1', 'true', 'yes'},
            'alert_min_total_delta': _int_env('CELERY_RECONCILIATION_ALERT_MIN_TOTAL_DELTA', 1),
            'alert_min_critical_delta': _int_env('CELERY_RECONCILIATION_ALERT_MIN_CRITICAL_DELTA', 1),
            'alert_stale_after_minutes': _int_env('CELERY_RECONCILIATION_ALERT_STALE_AFTER_MINUTES', 180),
        },
        'options': {'queue': OPS_QUEUE},
    },
    'trainerhub-ops-reconciliation-snapshot-prune': {
        'task': 'apps.ops.tasks.prune_reconciliation_snapshots_task',
        'schedule': _float_env('CELERY_RECONCILIATION_SNAPSHOT_PRUNE_EVERY_SECONDS', 86400.0),
        'kwargs': {
            'source': os.getenv('CELERY_RECONCILIATION_SNAPSHOT_RETENTION_SOURCE', ''),
            'scheduled_days': _int_env('CELERY_RECONCILIATION_SNAPSHOT_RETENTION_SCHEDULED_DAYS', 45),
            'repair_days': _int_env('CELERY_RECONCILIATION_SNAPSHOT_RETENTION_REPAIR_DAYS', 180),
            'manual_days': _int_env('CELERY_RECONCILIATION_SNAPSHOT_RETENTION_MANUAL_DAYS', 365),
            'ci_days': _int_env('CELERY_RECONCILIATION_SNAPSHOT_RETENTION_CI_DAYS', 14),
            'keep_min_per_source': _int_env('CELERY_RECONCILIATION_SNAPSHOT_RETENTION_KEEP_MIN_PER_SOURCE', 25),
            'max_candidates': _int_env('CELERY_RECONCILIATION_SNAPSHOT_RETENTION_MAX_CANDIDATES', 500),
            'dry_run': os.getenv('CELERY_RECONCILIATION_SNAPSHOT_RETENTION_DRY_RUN', 'false').lower() in {'1', 'true', 'yes'},
        },
        'options': {'queue': OPS_QUEUE},
    },
}


@app.task(bind=True, name='trainerhub.debug_task')
def debug_task(self):
    return {'task_id': self.request.id, 'name': self.name}
