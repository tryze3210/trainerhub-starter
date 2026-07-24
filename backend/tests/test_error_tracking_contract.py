from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_error_tracking_runtime_dependency_is_declared():
    requirements = (ROOT / 'backend' / 'requirements.txt').read_text()
    pyproject = (ROOT / 'backend' / 'pyproject.toml').read_text()

    assert 'sentry-sdk' in requirements
    assert 'sentry-sdk' in pyproject


def test_error_tracking_is_initialized_from_settings():
    integration = (ROOT / 'backend' / 'config' / 'error_tracking.py').read_text()
    settings = (ROOT / 'backend' / 'config' / 'settings' / 'base.py').read_text()

    assert 'sentry_sdk.init' in integration
    assert 'DjangoIntegration' in integration
    assert 'CeleryIntegration' in integration
    assert 'RedisIntegration' in integration
    assert 'configure_error_tracking(' in settings
    assert 'SENTRY_CONFIGURED = configure_error_tracking(' in settings
