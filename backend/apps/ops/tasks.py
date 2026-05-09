from __future__ import annotations

try:
    from celery import shared_task
except Exception:  # pragma: no cover - Celery is optional in some local test runs.
    shared_task = None


def _capture_scheduled_reconciliation_snapshot(
    *,
    limit: int = 100,
    source: str = 'scheduled',
    min_age_minutes: int = 60,
    force: bool = False,
    correlation_id: str = '',
    emit_alerts: bool = True,
    alert_min_total_delta: int = 1,
    alert_min_critical_delta: int = 1,
    alert_stale_after_minutes: int = 180,
) -> dict:
    from apps.ops.reconciliation_snapshots import (
        capture_reconciliation_snapshot_if_due,
        emit_reconciliation_snapshot_alerts,
        emit_reconciliation_snapshot_capture_failure_alert,
    )

    effective_correlation_id = correlation_id or 'celery:reconciliation_snapshot'
    try:
        payload = capture_reconciliation_snapshot_if_due(
            limit=limit,
            source=source,
            min_age_minutes=min_age_minutes,
            force=force,
            correlation_id=effective_correlation_id,
        )
    except Exception as exc:
        emit_reconciliation_snapshot_capture_failure_alert(
            error_message=str(exc),
            source=source,
            correlation_id=effective_correlation_id,
            notify_admins=emit_alerts,
        )
        raise

    if emit_alerts and payload.get('captured'):
        payload['alerts'] = emit_reconciliation_snapshot_alerts(
            source=source,
            min_total_delta=alert_min_total_delta,
            min_critical_delta=alert_min_critical_delta,
            stale_after_minutes=alert_stale_after_minutes,
            notify_admins=True,
        )
    elif emit_alerts:
        payload['alerts'] = {'status': 'skipped', 'reason': 'snapshot_not_captured'}
    return payload


def _prune_reconciliation_snapshots(
    *,
    source: str = '',
    scheduled_days: int = 45,
    repair_days: int = 180,
    manual_days: int = 365,
    ci_days: int = 14,
    keep_min_per_source: int = 25,
    max_candidates: int = 500,
    dry_run: bool = False,
) -> dict:
    from apps.ops.reconciliation_snapshots import prune_reconciliation_snapshots

    return prune_reconciliation_snapshots(
        source=source,
        scheduled_days=scheduled_days,
        repair_days=repair_days,
        manual_days=manual_days,
        ci_days=ci_days,
        keep_min_per_source=keep_min_per_source,
        max_candidates=max_candidates,
        include_candidates=False,
        dry_run=dry_run,
    )


if shared_task is not None:

    @shared_task(name='apps.ops.tasks.capture_reconciliation_snapshot_task', queue='ops')
    def capture_reconciliation_snapshot_task(
        limit: int = 100,
        source: str = 'scheduled',
        min_age_minutes: int = 60,
        force: bool = False,
        correlation_id: str = '',
        emit_alerts: bool = True,
        alert_min_total_delta: int = 1,
        alert_min_critical_delta: int = 1,
        alert_stale_after_minutes: int = 180,
    ) -> dict:
        return _capture_scheduled_reconciliation_snapshot(
            limit=limit,
            source=source,
            min_age_minutes=min_age_minutes,
            force=force,
            correlation_id=correlation_id,
            emit_alerts=emit_alerts,
            alert_min_total_delta=alert_min_total_delta,
            alert_min_critical_delta=alert_min_critical_delta,
            alert_stale_after_minutes=alert_stale_after_minutes,
        )

    @shared_task(name='apps.ops.tasks.prune_reconciliation_snapshots_task', queue='ops')
    def prune_reconciliation_snapshots_task(
        source: str = '',
        scheduled_days: int = 45,
        repair_days: int = 180,
        manual_days: int = 365,
        ci_days: int = 14,
        keep_min_per_source: int = 25,
        max_candidates: int = 500,
        dry_run: bool = False,
    ) -> dict:
        return _prune_reconciliation_snapshots(
            source=source,
            scheduled_days=scheduled_days,
            repair_days=repair_days,
            manual_days=manual_days,
            ci_days=ci_days,
            keep_min_per_source=keep_min_per_source,
            max_candidates=max_candidates,
            dry_run=dry_run,
        )

else:

    def capture_reconciliation_snapshot_task(
        limit: int = 100,
        source: str = 'scheduled',
        min_age_minutes: int = 60,
        force: bool = False,
        correlation_id: str = '',
        emit_alerts: bool = True,
        alert_min_total_delta: int = 1,
        alert_min_critical_delta: int = 1,
        alert_stale_after_minutes: int = 180,
    ) -> dict:
        return _capture_scheduled_reconciliation_snapshot(
            limit=limit,
            source=source,
            min_age_minutes=min_age_minutes,
            force=force,
            correlation_id=correlation_id,
            emit_alerts=emit_alerts,
            alert_min_total_delta=alert_min_total_delta,
            alert_min_critical_delta=alert_min_critical_delta,
            alert_stale_after_minutes=alert_stale_after_minutes,
        )

    def prune_reconciliation_snapshots_task(
        source: str = '',
        scheduled_days: int = 45,
        repair_days: int = 180,
        manual_days: int = 365,
        ci_days: int = 14,
        keep_min_per_source: int = 25,
        max_candidates: int = 500,
        dry_run: bool = False,
    ) -> dict:
        return _prune_reconciliation_snapshots(
            source=source,
            scheduled_days=scheduled_days,
            repair_days=repair_days,
            manual_days=manual_days,
            ci_days=ci_days,
            keep_min_per_source=keep_min_per_source,
            max_candidates=max_candidates,
            dry_run=dry_run,
        )
