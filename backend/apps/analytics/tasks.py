from celery import shared_task

from apps.analytics.services.kpi_builder import AnalyticsWarehouseBuilder


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def refresh_analytics_warehouse(self, days: int = 30, trigger: str = 'scheduled') -> int:
    builder = AnalyticsWarehouseBuilder()
    return builder.rebuild_last_n_days(days=days, trigger=trigger)
