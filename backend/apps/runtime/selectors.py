from __future__ import annotations

from datetime import datetime, timezone

from config.env import load_env


def health_payload() -> dict:
    return {
        'status': 'ok',
        'service': 'trainerhub-backend',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


def config_snapshot() -> dict:
    env = load_env()
    return {
        'env': env.env,
        'debug': env.debug,
        'allowed_hosts': env.allowed_hosts,
        'postgres': {
            'host': env.postgres_host,
            'port': env.postgres_port,
            'db': env.postgres_db,
            'user': env.postgres_user,
        },
        'redis_url': env.redis_url,
        'celery': {
            'broker_url': env.celery_broker_url,
            'result_backend': env.celery_result_backend,
        },
        'storage': {
            'bucket': env.vk_cloud_bucket,
            'region': env.vk_cloud_region,
            'endpoint': env.vk_cloud_endpoint,
        },
    }
