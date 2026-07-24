from __future__ import annotations

import pytest

from config.env import EnvError, load_env, validate_production_environment


def _secure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    values = {
        'APP_ENV': 'production',
        'DEBUG': '0',
        'SECRET_KEY': 'production-secret-key-with-strong-length-v167',
        'ALLOWED_HOSTS': 'trainerhub.example.com,api.trainerhub.example.com',
        'CSRF_TRUSTED_ORIGINS': 'https://trainerhub.example.com',
        'CORS_ALLOWED_ORIGINS': 'https://trainerhub.example.com',
        'API_BASE_URL': 'https://api.trainerhub.example.com',
        'FRONTEND_BASE_URL': 'https://trainerhub.example.com',
        'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
        'DEFAULT_FROM_EMAIL': 'TrainerHub <no-reply@trainerhub.example.com>',
        'EMAIL_HOST': 'smtp.trainerhub.example.com',
        'DATABASE_URL': 'postgres://trainerhub:secret@postgres:5432/trainerhub',
        'REDIS_URL': 'redis://redis:6379/0',
        'CACHE_URL': 'redis://redis:6379/0',
        'CELERY_BROKER_URL': 'redis://redis:6379/1',
        'CELERY_RESULT_BACKEND': 'redis://redis:6379/2',
        'CELERY_TASK_ALWAYS_EAGER': '0',
        'SENTRY_DSN': 'https://public@example.ingest.sentry.io/1',
        'VK_CLOUD_ENDPOINT': 'https://s3.trainerhub.example.com',
        'VK_CLOUD_ACCESS_KEY': 'vk-access-key-v167',
        'VK_CLOUD_SECRET_KEY': 'vk-secret-key-v167',
        'VK_PRIVATE_BUCKET': 'trainerhub-example-private',
        'VK_PUBLIC_BUCKET': 'trainerhub-example-public',
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_v167_production_env_rejects_debug() -> None:
    with pytest.raises(EnvError, match='DEBUG must be disabled'):
        validate_production_environment(
            env='production',
            debug=True,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
        )


def test_v167_production_env_rejects_wildcard_hosts() -> None:
    with pytest.raises(EnvError, match='ALLOWED_HOSTS'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['*'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
        )


def test_v167_production_env_rejects_placeholder_secrets() -> None:
    with pytest.raises(EnvError, match='SECRET_KEY'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='change-me',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
        )


def test_v167_production_env_rejects_empty_origins() -> None:
    with pytest.raises(EnvError, match='CSRF_TRUSTED_ORIGINS'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=[],
            cors_allowed_origins=['https://trainerhub.example.com'],
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
        )


def test_v167_production_env_rejects_http_csrf_origins() -> None:
    with pytest.raises(EnvError, match='CSRF_TRUSTED_ORIGINS'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['http://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
        )


def test_v167_production_env_rejects_http_cors_origins() -> None:
    with pytest.raises(EnvError, match='CORS_ALLOWED_ORIGINS'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['http://trainerhub.example.com'],
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
        )


def test_v167_production_env_rejects_missing_database_url() -> None:
    with pytest.raises(EnvError, match='DATABASE_URL'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            database_url='',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
        )


def test_v167_production_env_rejects_local_public_base_urls() -> None:
    with pytest.raises(EnvError, match='API_BASE_URL'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            api_base_url='http://localhost:8000',
            frontend_base_url='https://trainerhub.example.com',
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
        )

    with pytest.raises(EnvError, match='FRONTEND_BASE_URL'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            api_base_url='https://api.trainerhub.example.com',
            frontend_base_url='http://localhost:8080',
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
        )


def test_v167_production_env_rejects_unsafe_email_backend() -> None:
    with pytest.raises(EnvError, match='EMAIL_BACKEND'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            api_base_url='https://api.trainerhub.example.com',
            frontend_base_url='https://trainerhub.example.com',
            email_backend='django.core.mail.backends.console.EmailBackend',
            default_from_email='TrainerHub <no-reply@trainerhub.example.com>',
            email_host='smtp.trainerhub.example.com',
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
        )


def test_v167_production_env_rejects_local_email_sender_and_host() -> None:
    with pytest.raises(EnvError, match='DEFAULT_FROM_EMAIL'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            api_base_url='https://api.trainerhub.example.com',
            frontend_base_url='https://trainerhub.example.com',
            email_backend='django.core.mail.backends.smtp.EmailBackend',
            default_from_email='TrainerHub <no-reply@localhost>',
            email_host='smtp.trainerhub.example.com',
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
        )

    with pytest.raises(EnvError, match='EMAIL_HOST'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            api_base_url='https://api.trainerhub.example.com',
            frontend_base_url='https://trainerhub.example.com',
            email_backend='django.core.mail.backends.smtp.EmailBackend',
            default_from_email='TrainerHub <no-reply@trainerhub.example.com>',
            email_host='localhost',
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
        )


def test_v167_production_env_rejects_unsafe_storage_endpoint() -> None:
    with pytest.raises(EnvError, match='endpoint URL'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            api_base_url='https://api.trainerhub.example.com',
            frontend_base_url='https://trainerhub.example.com',
            email_backend='django.core.mail.backends.smtp.EmailBackend',
            default_from_email='TrainerHub <no-reply@trainerhub.example.com>',
            email_host='smtp.trainerhub.example.com',
            storage_endpoint_url='http://localhost:9000',
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
            storage_private_bucket='trainerhub-private',
            storage_public_bucket='trainerhub-public',
        )


def test_v167_production_env_rejects_missing_or_equal_storage_buckets() -> None:
    with pytest.raises(EnvError, match='private bucket'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            api_base_url='https://api.trainerhub.example.com',
            frontend_base_url='https://trainerhub.example.com',
            email_backend='django.core.mail.backends.smtp.EmailBackend',
            default_from_email='TrainerHub <no-reply@trainerhub.example.com>',
            email_host='smtp.trainerhub.example.com',
            storage_endpoint_url='https://s3.trainerhub.example.com',
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
            storage_private_bucket='',
            storage_public_bucket='trainerhub-public',
        )

    with pytest.raises(EnvError, match='must be different'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            api_base_url='https://api.trainerhub.example.com',
            frontend_base_url='https://trainerhub.example.com',
            email_backend='django.core.mail.backends.smtp.EmailBackend',
            default_from_email='TrainerHub <no-reply@trainerhub.example.com>',
            email_host='smtp.trainerhub.example.com',
            storage_endpoint_url='https://s3.trainerhub.example.com',
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
            storage_private_bucket='trainerhub-media',
            storage_public_bucket='trainerhub-media',
        )


def test_v167_production_env_rejects_local_cache_and_celery_urls() -> None:
    with pytest.raises(EnvError, match='REDIS_URL'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            api_base_url='https://api.trainerhub.example.com',
            frontend_base_url='https://trainerhub.example.com',
            email_backend='django.core.mail.backends.smtp.EmailBackend',
            default_from_email='TrainerHub <no-reply@trainerhub.example.com>',
            email_host='smtp.trainerhub.example.com',
            storage_endpoint_url='https://s3.trainerhub.example.com',
            redis_url='redis://localhost:6379/0',
            cache_url='redis://redis:6379/0',
            celery_broker_url='redis://redis:6379/1',
            celery_result_backend='redis://redis:6379/2',
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
            storage_private_bucket='trainerhub-private',
            storage_public_bucket='trainerhub-public',
        )

    with pytest.raises(EnvError, match='CELERY_BROKER_URL'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            api_base_url='https://api.trainerhub.example.com',
            frontend_base_url='https://trainerhub.example.com',
            email_backend='django.core.mail.backends.smtp.EmailBackend',
            default_from_email='TrainerHub <no-reply@trainerhub.example.com>',
            email_host='smtp.trainerhub.example.com',
            storage_endpoint_url='https://s3.trainerhub.example.com',
            redis_url='redis://redis:6379/0',
            cache_url='redis://redis:6379/0',
            celery_broker_url='redis://127.0.0.1:6379/1',
            celery_result_backend='redis://redis:6379/2',
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
            storage_private_bucket='trainerhub-private',
            storage_public_bucket='trainerhub-public',
        )


def test_v167_production_env_rejects_celery_eager_mode() -> None:
    with pytest.raises(EnvError, match='CELERY_TASK_ALWAYS_EAGER'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            api_base_url='https://api.trainerhub.example.com',
            frontend_base_url='https://trainerhub.example.com',
            email_backend='django.core.mail.backends.smtp.EmailBackend',
            default_from_email='TrainerHub <no-reply@trainerhub.example.com>',
            email_host='smtp.trainerhub.example.com',
            storage_endpoint_url='https://s3.trainerhub.example.com',
            redis_url='redis://redis:6379/0',
            cache_url='redis://redis:6379/0',
            celery_broker_url='redis://redis:6379/1',
            celery_result_backend='redis://redis:6379/2',
            celery_task_always_eager=True,
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
            storage_private_bucket='trainerhub-private',
            storage_public_bucket='trainerhub-public',
        )


def test_v167_production_env_rejects_missing_or_local_sentry_dsn() -> None:
    with pytest.raises(EnvError, match='SENTRY_DSN'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            api_base_url='https://api.trainerhub.example.com',
            frontend_base_url='https://trainerhub.example.com',
            email_backend='django.core.mail.backends.smtp.EmailBackend',
            default_from_email='TrainerHub <no-reply@trainerhub.example.com>',
            email_host='smtp.trainerhub.example.com',
            storage_endpoint_url='https://s3.trainerhub.example.com',
            redis_url='redis://redis:6379/0',
            cache_url='redis://redis:6379/0',
            celery_broker_url='redis://redis:6379/1',
            celery_result_backend='redis://redis:6379/2',
            sentry_dsn='',
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
            storage_private_bucket='trainerhub-private',
            storage_public_bucket='trainerhub-public',
        )

    with pytest.raises(EnvError, match='SENTRY_DSN'):
        validate_production_environment(
            env='production',
            debug=False,
            secret_key='production-secret-key-with-strong-length-v167',
            allowed_hosts=['trainerhub.example.com'],
            csrf_trusted_origins=['https://trainerhub.example.com'],
            cors_allowed_origins=['https://trainerhub.example.com'],
            api_base_url='https://api.trainerhub.example.com',
            frontend_base_url='https://trainerhub.example.com',
            email_backend='django.core.mail.backends.smtp.EmailBackend',
            default_from_email='TrainerHub <no-reply@trainerhub.example.com>',
            email_host='smtp.trainerhub.example.com',
            storage_endpoint_url='https://s3.trainerhub.example.com',
            redis_url='redis://redis:6379/0',
            cache_url='redis://redis:6379/0',
            celery_broker_url='redis://redis:6379/1',
            celery_result_backend='redis://redis:6379/2',
            sentry_dsn='http://localhost:9000/1',
            database_url='postgres://trainerhub:secret@postgres:5432/trainerhub',
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
            storage_private_bucket='trainerhub-private',
            storage_public_bucket='trainerhub-public',
        )


def test_v167_production_env_loads_security_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    _secure_env(monkeypatch)
    monkeypatch.setenv('SECURE_SSL_REDIRECT', '1')
    monkeypatch.setenv('SESSION_COOKIE_SECURE', '1')
    monkeypatch.setenv('CSRF_COOKIE_SECURE', '1')

    env = load_env()

    assert env.is_production is True
    assert env.debug is False
    assert env.allowed_hosts == ['trainerhub.example.com', 'api.trainerhub.example.com']
    assert env.api_base_url == 'https://api.trainerhub.example.com'
    assert env.frontend_base_url == 'https://trainerhub.example.com'
    assert env.email_backend == 'django.core.mail.backends.smtp.EmailBackend'
    assert env.default_from_email == 'TrainerHub <no-reply@trainerhub.example.com>'
    assert env.email_host == 'smtp.trainerhub.example.com'
    assert env.vk_cloud_endpoint == 'https://s3.trainerhub.example.com'
    assert env.vk_private_bucket == 'trainerhub-example-private'
    assert env.vk_public_bucket == 'trainerhub-example-public'
    assert env.redis_url == 'redis://redis:6379/0'
    assert env.cache_url == 'redis://redis:6379/0'
    assert env.celery_broker_url == 'redis://redis:6379/1'
    assert env.celery_result_backend == 'redis://redis:6379/2'
    assert env.sentry_dsn == 'https://public@example.ingest.sentry.io/1'
    assert env.csrf_trusted_origins == ['https://trainerhub.example.com']
    assert env.cors_allowed_origins == ['https://trainerhub.example.com']
    assert env.secure_ssl_redirect is True
    assert env.session_cookie_secure is True
    assert env.csrf_cookie_secure is True
