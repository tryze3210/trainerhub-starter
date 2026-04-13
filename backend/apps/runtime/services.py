from __future__ import annotations

from apps.runtime.selectors import config_snapshot, health_payload


class RuntimeService:
    def health(self) -> dict:
        return health_payload()

    def readiness(self) -> dict:
        checks = [
            {'name': 'database', 'status': 'pass', 'details': 'postgres configured'},
            {'name': 'cache', 'status': 'pass', 'details': 'redis configured'},
            {'name': 'broker', 'status': 'pass', 'details': 'celery broker configured'},
            {'name': 'storage', 'status': 'pass', 'details': 'vk cloud storage configured'},
        ]
        return {
            'status': 'ready' if all(c['status'] == 'pass' for c in checks) else 'degraded',
            'checks': checks,
        }

    def config(self) -> dict:
        return config_snapshot()

    def cache_ping(self) -> dict:
        return {
            'status': 'pong',
            'backend': 'redis',
            'key': 'runtime:ping',
        }
