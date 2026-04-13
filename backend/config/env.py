from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar('T')


class EnvError(RuntimeError):
    pass


@dataclass(frozen=True)
class AppEnv:
    env: str
    debug: bool
    secret_key: str
    allowed_hosts: list[str]
    api_base_url: str
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str
    sentry_dsn: str | None
    vk_cloud_bucket: str
    vk_cloud_region: str
    vk_cloud_endpoint: str
    vk_cloud_access_key: str
    vk_cloud_secret_key: str



def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def _parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(',') if item.strip()]


def _get(name: str, default: str | None = None, parser: Callable[[str], T] | None = None) -> T | str:
    raw = os.getenv(name, default)
    if raw is None:
        raise EnvError(f'Missing required env variable: {name}')
    return parser(raw) if parser else raw


def load_env() -> AppEnv:
    return AppEnv(
        env=str(_get('APP_ENV', 'local')),
        debug=bool(_get('DEBUG', '1', _parse_bool)),
        secret_key=str(_get('SECRET_KEY', 'change-me-in-production')),
        allowed_hosts=list(_get('ALLOWED_HOSTS', 'localhost,127.0.0.1', _parse_list)),
        api_base_url=str(_get('API_BASE_URL', 'http://localhost:8000')),
        postgres_db=str(_get('POSTGRES_DB', 'trainerhub')),
        postgres_user=str(_get('POSTGRES_USER', 'trainerhub')),
        postgres_password=str(_get('POSTGRES_PASSWORD', 'trainerhub')),
        postgres_host=str(_get('POSTGRES_HOST', 'postgres')),
        postgres_port=int(_get('POSTGRES_PORT', '5432')),
        redis_url=str(_get('REDIS_URL', 'redis://redis:6379/0')),
        celery_broker_url=str(_get('CELERY_BROKER_URL', 'redis://redis:6379/1')),
        celery_result_backend=str(_get('CELERY_RESULT_BACKEND', 'redis://redis:6379/2')),
        sentry_dsn=str(_get('SENTRY_DSN', '')) or None,
        vk_cloud_bucket=str(_get('VK_CLOUD_BUCKET', 'trainerhub-media')),
        vk_cloud_region=str(_get('VK_CLOUD_REGION', 'ru-msk')),
        vk_cloud_endpoint=str(_get('VK_CLOUD_ENDPOINT', 'https://hb.bizmrg.com')),
        vk_cloud_access_key=str(_get('VK_CLOUD_ACCESS_KEY', 'replace-me')),
        vk_cloud_secret_key=str(_get('VK_CLOUD_SECRET_KEY', 'replace-me')),
    )
