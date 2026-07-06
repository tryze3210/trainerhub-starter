from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar('T')
PRODUCTION_ENVS = {'production', 'prod'}
PLACEHOLDER_SECRETS = {'', 'change-me', 'change-me-in-production', 'replace-me'}


class EnvError(RuntimeError):
    pass


@dataclass(frozen=True)
class AppEnv:
    env: str
    debug: bool
    secret_key: str
    allowed_hosts: list[str]
    api_base_url: str
    csrf_trusted_origins: list[str]
    cors_allowed_origins: list[str]
    secure_ssl_redirect: bool
    session_cookie_secure: bool
    csrf_cookie_secure: bool
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

    @property
    def is_production(self) -> bool:
        return is_production_env(self.env)


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def _parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(',') if item.strip()]


def _get(
    name: str,
    default: str | None = None,
    parser: Callable[[str], T] | None = None,
) -> T | str:
    raw = os.getenv(name, default)
    if raw is None:
        raise EnvError(f'Missing required env variable: {name}')
    return parser(raw) if parser else raw


def is_production_env(env: str) -> bool:
    return env.strip().lower() in PRODUCTION_ENVS


def _has_placeholder(value: str | None) -> bool:
    return value is None or value.strip() in PLACEHOLDER_SECRETS


def validate_production_environment(
    *,
    env: str,
    debug: bool,
    secret_key: str,
    allowed_hosts: list[str],
    csrf_trusted_origins: list[str],
    cors_allowed_origins: list[str],
    storage_access_key: str | None = None,
    storage_secret_key: str | None = None,
) -> None:
    if not is_production_env(env):
        return

    errors: list[str] = []
    if debug:
        errors.append('DEBUG must be disabled when APP_ENV=production')
    if _has_placeholder(secret_key) or len(secret_key.strip()) < 32:
        errors.append('SECRET_KEY must be a non-placeholder value with at least 32 characters')
    if not allowed_hosts or '*' in allowed_hosts:
        errors.append('ALLOWED_HOSTS must list explicit production hosts')
    if not csrf_trusted_origins:
        errors.append('CSRF_TRUSTED_ORIGINS must list production frontend origins')
    if not cors_allowed_origins:
        errors.append('CORS_ALLOWED_ORIGINS must list production frontend origins')
    if _has_placeholder(storage_access_key):
        errors.append('VK/S3 access key must be configured for production')
    if _has_placeholder(storage_secret_key):
        errors.append('VK/S3 secret key must be configured for production')

    if errors:
        raise EnvError('Invalid production environment: ' + '; '.join(errors))


def load_env() -> AppEnv:
    env = AppEnv(
        env=str(_get('APP_ENV', 'local')),
        debug=bool(_get('DEBUG', '1', _parse_bool)),
        secret_key=str(_get('SECRET_KEY', 'change-me-in-production')),
        allowed_hosts=list(_get('ALLOWED_HOSTS', 'localhost,127.0.0.1', _parse_list)),
        api_base_url=str(_get('API_BASE_URL', 'http://localhost:8000')),
        csrf_trusted_origins=list(
            _get('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000', _parse_list)
        ),
        cors_allowed_origins=list(
            _get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000', _parse_list)
        ),
        secure_ssl_redirect=bool(_get('SECURE_SSL_REDIRECT', '0', _parse_bool)),
        session_cookie_secure=bool(_get('SESSION_COOKIE_SECURE', '0', _parse_bool)),
        csrf_cookie_secure=bool(_get('CSRF_COOKIE_SECURE', '0', _parse_bool)),
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
    validate_production_environment(
        env=env.env,
        debug=env.debug,
        secret_key=env.secret_key,
        allowed_hosts=env.allowed_hosts,
        csrf_trusted_origins=env.csrf_trusted_origins,
        cors_allowed_origins=env.cors_allowed_origins,
        storage_access_key=env.vk_cloud_access_key,
        storage_secret_key=env.vk_cloud_secret_key,
    )
    return env
