from __future__ import annotations

from typing import Any


def configure_error_tracking(
    *,
    dsn: str,
    environment: str,
    release: str | None = None,
    traces_sample_rate: float = 0.0,
) -> bool:
    if not dsn:
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
    except ImportError:
        return False

    options: dict[str, Any] = {
        'dsn': dsn,
        'environment': environment,
        'integrations': [
            DjangoIntegration(transaction_style='url'),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        'send_default_pii': False,
        'traces_sample_rate': traces_sample_rate,
    }
    if release:
        options['release'] = release

    sentry_sdk.init(**options)
    return True
