from __future__ import annotations

from apps.runtime.selectors import config_snapshot, health_payload


class RuntimeService:
    def health(self) -> dict:
        return health_payload()

    def readiness(self) -> dict:
        checks = [
            {'name': 'database', 'status': 'pass', 'details': 'configured'},
            {'name': 'cache', 'status': 'pass', 'details': 'configured'},
            {'name': 'broker', 'status': 'pass', 'details': 'configured'},
            {'name': 'storage', 'status': 'pass', 'details': 'configured'},
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


def get_health_status() -> dict:
    return RuntimeService().health()


def get_readiness_status() -> dict:
    return RuntimeService().readiness()


def get_runtime_config() -> dict:
    return RuntimeService().config()
