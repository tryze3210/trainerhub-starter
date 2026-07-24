from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, TypeVar
from urllib.parse import urlparse

T = TypeVar('T')
PRODUCTION_ENVS = {'production', 'prod'}
PLACEHOLDER_SECRETS = {'', 'change-me', 'change-me-in-production', 'replace-me'}
LOCAL_URL_HOSTS = {'localhost', '127.0.0.1', '0.0.0.0'}


class EnvError(RuntimeError):
    pass


@dataclass(frozen=True)
class AppEnv:
    env: str
    debug: bool
    secret_key: str
    allowed_hosts: list[str]
    api_base_url: str
    frontend_base_url: str
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
    cache_url: str
    celery_broker_url: str
    celery_result_backend: str
    sentry_dsn: str | None
    email_backend: str
    default_from_email: str
    email_host: str
    vk_cloud_bucket: str
    vk_cloud_region: str
    vk_cloud_endpoint: str
    vk_cloud_access_key: str
    vk_cloud_secret_key: str
    vk_private_bucket: str
    vk_public_bucket: str

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


def _is_public_https_url(value: str | None) -> bool:
    if _has_placeholder(value):
        return False
    parsed = urlparse(str(value).strip())
    return parsed.scheme == 'https' and bool(parsed.netloc) and (parsed.hostname or '').lower() not in LOCAL_URL_HOSTS


def _is_unsafe_email_sender(value: str | None) -> bool:
    normalized = (value or '').strip().lower()
    return not normalized or 'localhost' in normalized or '@example.' in normalized


def _is_local_host(value: str | None) -> bool:
    return (value or '').strip().lower() in LOCAL_URL_HOSTS


def _is_local_service_url(value: str | None) -> bool:
    if _has_placeholder(value):
        return True
    parsed = urlparse(str(value).strip())
    host = (parsed.hostname or '').lower()
    return not parsed.scheme or host in LOCAL_URL_HOSTS


def validate_production_environment(
    *,
    env: str,
    debug: bool,
    secret_key: str,
    allowed_hosts: list[str],
    csrf_trusted_origins: list[str],
    cors_allowed_origins: list[str],
    api_base_url: str | None = None,
    frontend_base_url: str | None = None,
    email_backend: str | None = None,
    default_from_email: str | None = None,
    email_host: str | None = None,
    storage_endpoint_url: str | None = None,
    redis_url: str | None = None,
    cache_url: str | None = None,
    celery_broker_url: str | None = None,
    celery_result_backend: str | None = None,
    celery_task_always_eager: bool = False,
    sentry_dsn: str | None = None,
    database_url: str | None = None,
    storage_access_key: str | None = None,
    storage_secret_key: str | None = None,
    storage_private_bucket: str | None = None,
    storage_public_bucket: str | None = None,
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
    if any(origin.strip().lower().startswith('http://') for origin in csrf_trusted_origins):
        errors.append('CSRF_TRUSTED_ORIGINS must use https:// origins in production')
    if not cors_allowed_origins:
        errors.append('CORS_ALLOWED_ORIGINS must list production frontend origins')
    if any(origin.strip().lower().startswith('http://') for origin in cors_allowed_origins):
        errors.append('CORS_ALLOWED_ORIGINS must use https:// origins in production')
    if not _is_public_https_url(api_base_url):
        errors.append('API_BASE_URL must be a public https:// URL in production')
    if not _is_public_https_url(frontend_base_url):
        errors.append('FRONTEND_BASE_URL must be a public https:// URL in production')
    normalized_email_backend = (email_backend or '').strip().lower()
    if not normalized_email_backend or any(marker in normalized_email_backend for marker in ('console', 'locmem', 'dummy')):
        errors.append('EMAIL_BACKEND must use a real transactional backend in production')
    if _is_unsafe_email_sender(default_from_email):
        errors.append('DEFAULT_FROM_EMAIL must use a production sender domain')
    if 'smtp' in normalized_email_backend and _is_local_host(email_host):
        errors.append('EMAIL_HOST must point to a production SMTP host')
    if _has_placeholder(database_url):
        errors.append('DATABASE_URL must point to a production PostgreSQL database')
    if not _is_public_https_url(storage_endpoint_url):
        errors.append('VK/S3 endpoint URL must be a public https:// URL in production')
    if _has_placeholder(storage_access_key):
        errors.append('VK/S3 access key must be configured for production')
    if _has_placeholder(storage_secret_key):
        errors.append('VK/S3 secret key must be configured for production')
    if _has_placeholder(storage_private_bucket):
        errors.append('VK/S3 private bucket must be configured for production')
    if _has_placeholder(storage_public_bucket):
        errors.append('VK/S3 public bucket must be configured for production')
    if storage_private_bucket and storage_public_bucket and storage_private_bucket == storage_public_bucket:
        errors.append('VK/S3 private and public buckets must be different in production')
    if _is_local_service_url(redis_url):
        errors.append('REDIS_URL must point to a shared production Redis service')
    if _is_local_service_url(cache_url):
        errors.append('CACHE_URL must point to a shared production cache service')
    if _is_local_service_url(celery_broker_url):
        errors.append('CELERY_BROKER_URL must point to a shared production broker')
    if _is_local_service_url(celery_result_backend):
        errors.append('CELERY_RESULT_BACKEND must point to a shared production result backend')
    if celery_task_always_eager:
        errors.append('CELERY_TASK_ALWAYS_EAGER must be disabled in production')
    if not _is_public_https_url(sentry_dsn):
        errors.append('SENTRY_DSN must be configured with a public https:// DSN in production')

    if errors:
        raise EnvError('Invalid production environment: ' + '; '.join(errors))


def load_env() -> AppEnv:
    env = AppEnv(
        env=str(_get('APP_ENV', 'local')),
        debug=bool(_get('DEBUG', '1', _parse_bool)),
        secret_key=str(_get('SECRET_KEY', 'change-me-in-production')),
        allowed_hosts=list(_get('ALLOWED_HOSTS', 'localhost,127.0.0.1', _parse_list)),
        api_base_url=str(_get('API_BASE_URL', 'http://localhost:8000')),
        frontend_base_url=str(_get('FRONTEND_BASE_URL', _get('NEXT_PUBLIC_APP_URL', 'http://localhost:3000'))),
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
        cache_url=str(_get('CACHE_URL', _get('REDIS_URL', 'redis://redis:6379/0'))),
        celery_broker_url=str(_get('CELERY_BROKER_URL', 'redis://redis:6379/1')),
        celery_result_backend=str(_get('CELERY_RESULT_BACKEND', 'redis://redis:6379/2')),
        sentry_dsn=str(_get('SENTRY_DSN', '')) or None,
        email_backend=str(_get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')),
        default_from_email=str(_get('DEFAULT_FROM_EMAIL', 'TrainerHub <no-reply@localhost>')),
        email_host=str(_get('EMAIL_HOST', 'localhost')),
        vk_cloud_bucket=str(_get('VK_CLOUD_BUCKET', 'trainerhub-media')),
        vk_cloud_region=str(_get('VK_CLOUD_REGION', 'ru-msk')),
        vk_cloud_endpoint=str(_get('VK_CLOUD_ENDPOINT', 'https://hb.bizmrg.com')),
        vk_cloud_access_key=str(_get('VK_CLOUD_ACCESS_KEY', 'replace-me')),
        vk_cloud_secret_key=str(_get('VK_CLOUD_SECRET_KEY', 'replace-me')),
        vk_private_bucket=str(_get('VK_PRIVATE_BUCKET', 'trainerhub-private')),
        vk_public_bucket=str(_get('VK_PUBLIC_BUCKET', 'trainerhub-public')),
    )
    validate_production_environment(
        env=env.env,
        debug=env.debug,
        secret_key=env.secret_key,
        allowed_hosts=env.allowed_hosts,
        csrf_trusted_origins=env.csrf_trusted_origins,
        cors_allowed_origins=env.cors_allowed_origins,
        api_base_url=env.api_base_url,
        frontend_base_url=env.frontend_base_url,
        email_backend=env.email_backend,
        default_from_email=env.default_from_email,
        email_host=env.email_host,
        storage_endpoint_url=env.vk_cloud_endpoint,
        redis_url=env.redis_url,
        cache_url=env.cache_url,
        celery_broker_url=env.celery_broker_url,
        celery_result_backend=env.celery_result_backend,
        celery_task_always_eager=bool(os.getenv('CELERY_TASK_ALWAYS_EAGER', '').strip().lower() in {'1', 'true', 'yes', 'on'}),
        sentry_dsn=env.sentry_dsn,
        database_url=os.getenv('DATABASE_URL'),
        storage_access_key=env.vk_cloud_access_key,
        storage_secret_key=env.vk_cloud_secret_key,
        storage_private_bucket=env.vk_private_bucket,
        storage_public_bucket=env.vk_public_bucket,
    )
    return env
