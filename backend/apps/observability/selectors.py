from __future__ import annotations

from apps.observability.models import LogRecord, MetricSample, TraceSpan

METRICS: list[MetricSample] = [
    MetricSample(key='http_requests_per_minute', value=1842, unit='rpm', status='healthy', labels={'service': 'api'}),
    MetricSample(key='celery_queue_lag_seconds', value=12, unit='seconds', status='warning', labels={'queue': 'media'}),
    MetricSample(key='projection_rebuild_failures_total', value=2, unit='count', status='warning', labels={'projection': 'public_catalog'}),
    MetricSample(key='payment_webhook_success_rate', value=99.4, unit='percent', status='healthy', labels={'provider': 'stub_psp'}),
]

LOGS: list[LogRecord] = [
    LogRecord(id='log_001', level='INFO', service='payments', message='Webhook finalized payment successfully', correlation_id='corr_pay_1001', context={'payment_id': 'pay_1001'}),
    LogRecord(id='log_002', level='WARNING', service='projections', message='Projection lag exceeds threshold', correlation_id='corr_proj_3001', context={'projection_key': 'public_catalog'}),
    LogRecord(id='log_003', level='ERROR', service='media', message='Transcode retry scheduled', correlation_id='corr_media_2001', context={'asset_id': 'asset_2001'}),
]

TRACES: list[TraceSpan] = [
    TraceSpan(trace_id='trace_001', span_id='span_001', parent_span_id=None, operation='payments.webhook.finalize', service='payments', status='ok', duration_ms=142, correlation_id='corr_pay_1001', tags={'payment_id': 'pay_1001'}),
    TraceSpan(trace_id='trace_002', span_id='span_002', parent_span_id='span_001', operation='orders.mark_paid', service='orders', status='ok', duration_ms=24, correlation_id='corr_pay_1001', tags={'order_id': 'ord_5001'}),
    TraceSpan(trace_id='trace_003', span_id='span_003', parent_span_id=None, operation='projections.public_catalog.rebuild', service='projections', status='warning', duration_ms=731, correlation_id='corr_proj_3001', tags={'projection_key': 'public_catalog'}),
]


def list_metrics() -> list[MetricSample]:
    return METRICS


def list_logs() -> list[LogRecord]:
    return LOGS


def list_traces() -> list[TraceSpan]:
    return TRACES
