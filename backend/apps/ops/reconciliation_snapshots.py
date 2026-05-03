from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.db.models import Count
from django.utils import timezone

from apps.ops.models import ReconciliationSnapshot
from apps.ops.reconciliation import get_money_reconciliation_report


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value.quantize(Decimal('0.01')))
    if isinstance(value, UUID):
        return str(value)
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value


def _actor_from_request(request):
    user = getattr(request, 'user', None)
    if getattr(user, 'is_authenticated', False):
        return user
    return None


def _snapshot_href(snapshot_id: Any) -> str:
    return f'/admin/entities/reconciliation_snapshot/{snapshot_id}'


def _section_statuses(report: dict[str, Any]) -> dict[str, Any]:
    sections = report.get('sections') or {}
    return {
        key: {
            'status': section.get('status', 'unknown'),
            'issue_count': int(section.get('issue_count') or 0),
            'critical_count': sum(1 for issue in section.get('issues') or [] if issue.get('severity') == 'critical'),
            'warning_count': sum(1 for issue in section.get('issues') or [] if issue.get('severity') == 'warning'),
        }
        for key, section in sections.items()
    }


def _delta(current: ReconciliationSnapshot, previous: ReconciliationSnapshot | None) -> dict[str, Any]:
    if previous is None:
        return {
            'has_previous': False,
            'total_issues_delta': 0,
            'critical_count_delta': 0,
            'warning_count_delta': 0,
            'direction': 'baseline',
        }
    total_delta = int(current.total_issues) - int(previous.total_issues)
    critical_delta = int(current.critical_count) - int(previous.critical_count)
    warning_delta = int(current.warning_count) - int(previous.warning_count)
    if critical_delta < 0 or (critical_delta == 0 and total_delta < 0):
        direction = 'improved'
    elif critical_delta > 0 or total_delta > 0:
        direction = 'worsened'
    else:
        direction = 'unchanged'
    return {
        'has_previous': True,
        'previous_snapshot_id': str(previous.id),
        'previous_generated_at': previous.generated_at.isoformat() if previous.generated_at else None,
        'total_issues_delta': total_delta,
        'critical_count_delta': critical_delta,
        'warning_count_delta': warning_delta,
        'direction': direction,
    }


def _snapshot_to_dict(snapshot: ReconciliationSnapshot, *, include_report: bool = False, previous: ReconciliationSnapshot | None = None) -> dict[str, Any]:
    payload = {
        'id': str(snapshot.id),
        'href': _snapshot_href(snapshot.id),
        'status': snapshot.status,
        'source': snapshot.source,
        'generated_at': snapshot.generated_at,
        'created_at': snapshot.created_at,
        'created_by': str(snapshot.created_by_id) if snapshot.created_by_id else None,
        'correlation_id': snapshot.correlation_id,
        'summary': snapshot.summary or {},
        'section_statuses': snapshot.section_statuses or {},
        'total_issues': snapshot.total_issues,
        'critical_count': snapshot.critical_count,
        'warning_count': snapshot.warning_count,
        'info_count': snapshot.info_count,
        'delta': _delta(snapshot, previous),
    }
    if include_report:
        payload['report'] = snapshot.report or {}
    return _json_safe(payload)


class ReconciliationSnapshotService:
    """Captures and reads scheduled reconciliation snapshots."""

    DEFAULT_LIMIT = 100

    def capture(
        self,
        *,
        limit: int = DEFAULT_LIMIT,
        source: str = ReconciliationSnapshot.Source.MANUAL,
        correlation_id: str = '',
        actor=None,
        request=None,
    ) -> dict[str, Any]:
        limit = max(1, min(int(limit or self.DEFAULT_LIMIT), 500))
        if source not in ReconciliationSnapshot.Source.values:
            source = ReconciliationSnapshot.Source.MANUAL

        report = get_money_reconciliation_report(limit=limit)
        summary = report.get('summary') or {}
        section_statuses = _section_statuses(report)
        snapshot = ReconciliationSnapshot.objects.create(
            status=report.get('status') or ReconciliationSnapshot.Status.OK,
            source=source,
            generated_at=timezone.now(),
            created_by=actor or _actor_from_request(request),
            correlation_id=correlation_id or getattr(request, 'headers', {}).get('X-Correlation-ID', '') if request else correlation_id,
            total_issues=int(summary.get('total_issues') or 0),
            critical_count=int(summary.get('critical_count') or 0),
            warning_count=int(summary.get('warning_count') or 0),
            info_count=int(summary.get('info_count') or 0),
            summary=_json_safe(summary),
            section_statuses=_json_safe(section_statuses),
            report=_json_safe(report),
        )
        previous = ReconciliationSnapshot.objects.exclude(pk=snapshot.pk).order_by('-generated_at', '-created_at').first()
        payload = _snapshot_to_dict(snapshot, include_report=True, previous=previous)

        if request is not None:
            try:
                from apps.audit.services import AuditService

                audit_event = AuditService.log_admin_action(
                    request=request,
                    action='reconciliation.snapshot.capture',
                    target_type='reconciliation_snapshot',
                    target_id=str(snapshot.id),
                    reason=f'{source}:reconciliation_snapshot_capture',
                    status=payload['status'],
                    context={'snapshot': payload, 'limit': limit},
                )
                payload['audit_event_id'] = str(audit_event.id)
                payload['audit_event_href'] = f'/admin/entities/audit_event/{audit_event.id}'
            except Exception:
                # Snapshot capture must not fail because audit logging failed.
                payload['audit_event_id'] = ''
                payload['audit_event_href'] = ''
        return payload

    def list(self, *, limit: int = 20, source: str = '', status: str = '', include_report: bool = False) -> dict[str, Any]:
        limit = max(1, min(int(limit or 20), 250))
        qs = ReconciliationSnapshot.objects.all().order_by('-generated_at', '-created_at')
        if source:
            qs = qs.filter(source=source)
        if status:
            qs = qs.filter(status=status)
        rows = list(qs[:limit])
        previous_by_id: dict[str, ReconciliationSnapshot | None] = {}
        all_for_delta = list(qs[: limit + 1])
        for index, item in enumerate(all_for_delta):
            previous_by_id[str(item.id)] = all_for_delta[index + 1] if index + 1 < len(all_for_delta) else None
        snapshots = [
            _snapshot_to_dict(item, include_report=include_report, previous=previous_by_id.get(str(item.id)))
            for item in rows
        ]
        return {
            'status': 'ok',
            'generated_at': timezone.now(),
            'count': len(snapshots),
            'filters': {'limit': limit, 'source': source, 'status': status, 'include_report': include_report},
            'summary': self.summary(),
            'snapshots': snapshots,
        }

    def summary(self) -> dict[str, Any]:
        latest = ReconciliationSnapshot.objects.order_by('-generated_at', '-created_at').first()
        by_status = list(ReconciliationSnapshot.objects.values('status').annotate(count=Count('id')).order_by('status'))
        by_source = list(ReconciliationSnapshot.objects.values('source').annotate(count=Count('id')).order_by('source'))
        return _json_safe({
            'latest_snapshot_id': str(latest.id) if latest else None,
            'latest_status': latest.status if latest else 'missing',
            'latest_generated_at': latest.generated_at if latest else None,
            'latest_total_issues': latest.total_issues if latest else 0,
            'latest_critical_count': latest.critical_count if latest else 0,
            'snapshot_count': ReconciliationSnapshot.objects.count(),
            'by_status': by_status,
            'by_source': by_source,
        })

    def trend(self, *, limit: int = 30) -> dict[str, Any]:
        limit = max(2, min(int(limit or 30), 250))
        rows = list(ReconciliationSnapshot.objects.order_by('-generated_at', '-created_at')[:limit])
        chronological = list(reversed(rows))
        points = [
            _json_safe({
                'id': snapshot.id,
                'status': snapshot.status,
                'source': snapshot.source,
                'generated_at': snapshot.generated_at,
                'total_issues': snapshot.total_issues,
                'critical_count': snapshot.critical_count,
                'warning_count': snapshot.warning_count,
                'info_count': snapshot.info_count,
            })
            for snapshot in chronological
        ]
        latest = rows[0] if rows else None
        previous = rows[1] if len(rows) > 1 else None
        return _json_safe({
            'status': latest.status if latest else 'missing',
            'generated_at': timezone.now(),
            'summary': self.summary(),
            'delta': _delta(latest, previous) if latest else {},
            'points': points,
        })


def capture_reconciliation_snapshot(**kwargs) -> dict[str, Any]:
    return ReconciliationSnapshotService().capture(**kwargs)


def list_reconciliation_snapshots(**kwargs) -> dict[str, Any]:
    return ReconciliationSnapshotService().list(**kwargs)


def get_reconciliation_snapshot_trend(**kwargs) -> dict[str, Any]:
    return ReconciliationSnapshotService().trend(**kwargs)
