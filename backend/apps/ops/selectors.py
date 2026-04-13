from __future__ import annotations

from apps.ops.models import DiagnosticsCheck, DiagnosticsRun

DIAGNOSTICS_CHECKS: list[DiagnosticsCheck] = [
    DiagnosticsCheck(key='db_connectivity', title='Postgres connectivity', status='ok', severity='high', message='Primary database reachable', owner='platform'),
    DiagnosticsCheck(key='redis_ping', title='Redis ping', status='ok', severity='high', message='Broker/cache responds to ping', owner='platform'),
    DiagnosticsCheck(key='celery_workers', title='Celery workers', status='warning', severity='medium', message='Media queue has reduced worker capacity', owner='platform'),
    DiagnosticsCheck(key='object_storage_signer', title='VK Cloud signer', status='warning', severity='medium', message='Signer is placeholder in scaffold', owner='media'),
]

DIAGNOSTICS_RUNS: list[DiagnosticsRun] = []


def list_checks() -> list[DiagnosticsCheck]:
    return DIAGNOSTICS_CHECKS


def list_runs() -> list[DiagnosticsRun]:
    return DIAGNOSTICS_RUNS
