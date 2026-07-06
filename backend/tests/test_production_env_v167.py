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
        'VK_CLOUD_ACCESS_KEY': 'vk-access-key-v167',
        'VK_CLOUD_SECRET_KEY': 'vk-secret-key-v167',
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
            storage_access_key='vk-access-key-v167',
            storage_secret_key='vk-secret-key-v167',
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
    assert env.csrf_trusted_origins == ['https://trainerhub.example.com']
    assert env.cors_allowed_origins == ['https://trainerhub.example.com']
    assert env.secure_ssl_redirect is True
    assert env.session_cookie_secure is True
    assert env.csrf_cookie_secure is True
