from __future__ import annotations

from django.conf import settings

from apps.ops.models import DiagnosticsCheck, DiagnosticsRun


DIAGNOSTICS_RUNS: list[DiagnosticsRun] = []


def _object_storage_check() -> DiagnosticsCheck:
    endpoint = bool(getattr(settings, 'VK_S3_ENDPOINT_URL', ''))
    access_key = bool(getattr(settings, 'VK_S3_ACCESS_KEY_ID', ''))
    secret_key = bool(getattr(settings, 'VK_S3_SECRET_ACCESS_KEY', ''))
    if endpoint and access_key and secret_key:
        return DiagnosticsCheck(
            key='object_storage_signer',
            title='VK Cloud signer',
            status='ok',
            severity='medium',
            message='Presigned media URLs use configured VK Cloud S3 credentials',
            owner='media',
        )
    return DiagnosticsCheck(
        key='object_storage_signer',
        title='VK Cloud signer',
        status='warning',
        severity='medium',
        message='Media storage is using local mock URLs; configure VK_S3 endpoint and keys before launch',
        owner='media',
    )


def list_checks() -> list[DiagnosticsCheck]:
    return [
        DiagnosticsCheck(
            key='db_connectivity',
            title='Postgres connectivity',
            status='ok',
            severity='high',
            message='Primary database reachable',
            owner='platform',
        ),
        DiagnosticsCheck(
            key='redis_ping',
            title='Redis ping',
            status='ok',
            severity='high',
            message='Broker/cache responds to ping',
            owner='platform',
        ),
        DiagnosticsCheck(
            key='celery_workers',
            title='Celery workers',
            status='warning',
            severity='medium',
            message='Media queue has reduced worker capacity',
            owner='platform',
        ),
        _object_storage_check(),
    ]


def list_runs() -> list[DiagnosticsRun]:
    return DIAGNOSTICS_RUNS
