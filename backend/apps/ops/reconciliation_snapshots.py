from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
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


def _request_correlation_id(request) -> str:
    if request is None:
        return ''
    headers = getattr(request, 'headers', None)
    if headers is None:
        return ''
    return headers.get('X-Correlation-ID', '')


def _snapshot_href(snapshot_id: Any) -> str:
    return f'/admin/entities/reconciliation_snapshot/{snapshot_id}'


def _issue_severity_counts(issues: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for issue in issues:
        counts[str(issue.get('severity') or 'info')] += 1
    return {
        'critical_count': int(counts.get('critical', 0)),
        'warning_count': int(counts.get('warning', 0)),
        'info_count': int(counts.get('info', 0)),
    }


def _section_issue_counts(section: dict[str, Any] | None) -> dict[str, Any]:
    section = section or {}
    issues = list(section.get('issues') or [])
    severity_counts = _issue_severity_counts(issues)
    return {
        'status': section.get('status', 'unknown'),
        'issue_count': int(section.get('issue_count') if section.get('issue_count') is not None else len(issues)),
        **severity_counts,
    }


def _section_statuses(report: dict[str, Any]) -> dict[str, Any]:
    sections = report.get('sections') or {}
    return {key: _section_issue_counts(section) for key, section in sections.items()}


def _direction_from_deltas(*, total_delta: int, critical_delta: int) -> str:
    if critical_delta < 0 or (critical_delta == 0 and total_delta < 0):
        return 'improved'
    if critical_delta > 0 or total_delta > 0:
        return 'worsened'
    return 'unchanged'


def _delta(current: ReconciliationSnapshot, previous: ReconciliationSnapshot | None) -> dict[str, Any]:
    if previous is None:
        return {
            'has_previous': False,
            'total_issues_delta': 0,
            'critical_count_delta': 0,
            'warning_count_delta': 0,
            'info_count_delta': 0,
            'direction': 'baseline',
        }

    total_delta = int(current.total_issues) - int(previous.total_issues)
    critical_delta = int(current.critical_count) - int(previous.critical_count)
    warning_delta = int(current.warning_count) - int(previous.warning_count)
    info_delta = int(current.info_count) - int(previous.info_count)

    return {
        'has_previous': True,
        'previous_snapshot_id': str(previous.id),
        'previous_generated_at': previous.generated_at.isoformat() if previous.generated_at else None,
        'total_issues_delta': total_delta,
        'critical_count_delta': critical_delta,
        'warning_count_delta': warning_delta,
        'info_count_delta': info_delta,
        'direction': _direction_from_deltas(total_delta=total_delta, critical_delta=critical_delta),
    }


def _snapshot_to_dict(
    snapshot: ReconciliationSnapshot,
    *,
    include_report: bool = False,
    previous: ReconciliationSnapshot | None = None,
) -> dict[str, Any]:
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


def _iter_snapshot_issues(snapshot: ReconciliationSnapshot | None) -> list[dict[str, Any]]:
    if snapshot is None:
        return []
    report = snapshot.report or {}
    sections = report.get('sections') or {}
    result: list[dict[str, Any]] = []
    for section_key, section in sections.items():
        for issue in section.get('issues') or []:
            item = dict(issue)
            item.setdefault('section', section_key)
            result.append(item)
    return result


def _issue_identity(issue: dict[str, Any]) -> str:
    return ':'.join(
        [
            str(issue.get('code') or 'unknown'),
            str(issue.get('entity_type') or 'unknown'),
            str(issue.get('entity_id') or ''),
        ]
    )


def _issues_by_identity(snapshot: ReconciliationSnapshot | None) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for issue in _iter_snapshot_issues(snapshot):
        rows[_issue_identity(issue)] = issue
    return rows


def _issue_summary(issue: dict[str, Any]) -> dict[str, Any]:
    return _json_safe(
        {
            'identity': _issue_identity(issue),
            'code': issue.get('code'),
            'severity': issue.get('severity'),
            'section': issue.get('section'),
            'entity_type': issue.get('entity_type'),
            'entity_id': issue.get('entity_id'),
            'message': issue.get('message'),
            'suggested_action': issue.get('suggested_action'),
            'related': issue.get('related') or [],
            'evidence': issue.get('evidence') or {},
        }
    )


def _section_diffs(
    *,
    current: ReconciliationSnapshot,
    baseline: ReconciliationSnapshot | None,
) -> list[dict[str, Any]]:
    current_sections = ((current.report or {}).get('sections') or {}) if current else {}
    baseline_sections = ((baseline.report or {}).get('sections') or {}) if baseline else {}
    section_keys = sorted(set(current_sections.keys()) | set(baseline_sections.keys()))
    rows: list[dict[str, Any]] = []

    for section_key in section_keys:
        current_counts = _section_issue_counts(current_sections.get(section_key))
        baseline_counts = _section_issue_counts(baseline_sections.get(section_key))
        total_delta = int(current_counts['issue_count']) - int(baseline_counts['issue_count'])
        critical_delta = int(current_counts['critical_count']) - int(baseline_counts['critical_count'])
        rows.append(
            {
                'section': section_key,
                'baseline_status': baseline_counts['status'],
                'current_status': current_counts['status'],
                'baseline_issue_count': baseline_counts['issue_count'],
                'current_issue_count': current_counts['issue_count'],
                'issue_count_delta': total_delta,
                'critical_count_delta': critical_delta,
                'warning_count_delta': int(current_counts['warning_count']) - int(baseline_counts['warning_count']),
                'info_count_delta': int(current_counts['info_count']) - int(baseline_counts['info_count']),
                'direction': _direction_from_deltas(total_delta=total_delta, critical_delta=critical_delta),
            }
        )

    return _json_safe(rows)


def _compare_snapshot_payload(
    *,
    current: ReconciliationSnapshot,
    baseline: ReconciliationSnapshot | None,
    include_report: bool = False,
    diff_limit: int = 100,
) -> dict[str, Any]:
    diff_limit = max(1, min(int(diff_limit or 100), 500))
    current_issues = _issues_by_identity(current)
    baseline_issues = _issues_by_identity(baseline)

    current_keys = set(current_issues.keys())
    baseline_keys = set(baseline_issues.keys())
    resolved_keys = sorted(baseline_keys - current_keys)
    introduced_keys = sorted(current_keys - baseline_keys)
    persisted_keys = sorted(current_keys & baseline_keys)
    severity_changed_keys = sorted(
        key
        for key in persisted_keys
        if str(current_issues[key].get('severity')) != str(baseline_issues[key].get('severity'))
    )

    delta = _delta(current, baseline)
    payload = {
        'status': current.status,
        'generated_at': timezone.now(),
        'has_baseline': baseline is not None,
        'baseline_snapshot': _snapshot_to_dict(baseline, include_report=include_report) if baseline else None,
        'current_snapshot': _snapshot_to_dict(current, include_report=include_report, previous=baseline),
        'delta': delta,
        'section_diffs': _section_diffs(current=current, baseline=baseline),
        'issue_diffs': {
            'resolved_count': len(resolved_keys),
            'introduced_count': len(introduced_keys),
            'persisted_count': len(persisted_keys),
            'severity_changed_count': len(severity_changed_keys),
            'resolved': [_issue_summary(baseline_issues[key]) for key in resolved_keys[:diff_limit]],
            'introduced': [_issue_summary(current_issues[key]) for key in introduced_keys[:diff_limit]],
            'persisted': [_issue_summary(current_issues[key]) for key in persisted_keys[:diff_limit]],
            'severity_changed': [
                {
                    'identity': key,
                    'baseline': _issue_summary(baseline_issues[key]),
                    'current': _issue_summary(current_issues[key]),
                }
                for key in severity_changed_keys[:diff_limit]
            ],
            'truncated': any(
                len(keys) > diff_limit
                for keys in (resolved_keys, introduced_keys, persisted_keys, severity_changed_keys)
            ),
            'limit': diff_limit,
        },
    }
    return _json_safe(payload)



def _window_issue_totals(rows: list[ReconciliationSnapshot]) -> dict[str, int]:
    return {
        'total_issues': sum(int(item.total_issues or 0) for item in rows),
        'critical_count': sum(int(item.critical_count or 0) for item in rows),
        'warning_count': sum(int(item.warning_count or 0) for item in rows),
        'info_count': sum(int(item.info_count or 0) for item in rows),
    }


def _snapshot_metric_point(
    snapshot: ReconciliationSnapshot,
    previous: ReconciliationSnapshot | None = None,
) -> dict[str, Any]:
    return _json_safe(
        {
            'id': snapshot.id,
            'href': _snapshot_href(snapshot.id),
            'status': snapshot.status,
            'source': snapshot.source,
            'generated_at': snapshot.generated_at,
            'total_issues': snapshot.total_issues,
            'critical_count': snapshot.critical_count,
            'warning_count': snapshot.warning_count,
            'info_count': snapshot.info_count,
            'delta': _delta(snapshot, previous),
        }
    )


def _latest_section_metrics(
    *,
    current: ReconciliationSnapshot | None,
    previous: ReconciliationSnapshot | None,
) -> list[dict[str, Any]]:
    if current is None:
        return []

    current_sections = current.section_statuses or _section_statuses(current.report or {})
    previous_sections = (previous.section_statuses or _section_statuses(previous.report or {})) if previous else {}
    section_keys = sorted(set(current_sections.keys()) | set(previous_sections.keys()))
    result: list[dict[str, Any]] = []

    for section_key in section_keys:
        current_counts = _section_issue_counts(current_sections.get(section_key))
        previous_counts = _section_issue_counts(previous_sections.get(section_key)) if previous else {
            'status': 'missing',
            'issue_count': 0,
            'critical_count': 0,
            'warning_count': 0,
            'info_count': 0,
        }
        issue_delta = int(current_counts['issue_count']) - int(previous_counts['issue_count'])
        critical_delta = int(current_counts['critical_count']) - int(previous_counts['critical_count'])
        result.append(
            {
                'section': section_key,
                'status': current_counts['status'],
                'previous_status': previous_counts['status'],
                'issue_count': current_counts['issue_count'],
                'critical_count': current_counts['critical_count'],
                'warning_count': current_counts['warning_count'],
                'info_count': current_counts['info_count'],
                'issue_count_delta': issue_delta,
                'critical_count_delta': critical_delta,
                'warning_count_delta': int(current_counts['warning_count']) - int(previous_counts['warning_count']),
                'info_count_delta': int(current_counts['info_count']) - int(previous_counts['info_count']),
                'direction': _direction_from_deltas(total_delta=issue_delta, critical_delta=critical_delta),
            }
        )

    return _json_safe(result)


def _trend_metric_points(rows_desc: list[ReconciliationSnapshot]) -> list[dict[str, Any]]:
    chronological = list(reversed(rows_desc))
    points: list[dict[str, Any]] = []
    previous: ReconciliationSnapshot | None = None
    for snapshot in chronological:
        points.append(_snapshot_metric_point(snapshot, previous))
        previous = snapshot
    return points


def _repair_effectiveness_metrics(*, status: str = '', limit: int = 25) -> dict[str, Any]:
    repair_qs = ReconciliationSnapshot.objects.filter(source=ReconciliationSnapshot.Source.REPAIR).order_by(
        '-generated_at',
        '-created_at',
    )
    if status:
        repair_qs = repair_qs.filter(status=status)

    repair_rows = list(repair_qs[: max(1, min(int(limit or 25), 50))])
    direction_counts: dict[str, int] = defaultdict(int)
    items: list[dict[str, Any]] = []

    for snapshot in repair_rows:
        previous = (
            ReconciliationSnapshot.objects.exclude(pk=snapshot.pk)
            .filter(generated_at__lte=snapshot.generated_at)
            .order_by('-generated_at', '-created_at')
            .first()
        )
        if previous is None:
            previous = ReconciliationSnapshot.objects.exclude(pk=snapshot.pk).order_by('-generated_at', '-created_at').first()
        delta = _delta(snapshot, previous)
        direction = str(delta.get('direction') or 'baseline')
        direction_counts[direction] += 1
        items.append(
            _json_safe(
                {
                    'id': snapshot.id,
                    'href': _snapshot_href(snapshot.id),
                    'generated_at': snapshot.generated_at,
                    'status': snapshot.status,
                    'total_issues': snapshot.total_issues,
                    'critical_count': snapshot.critical_count,
                    'delta': delta,
                }
            )
        )

    return _json_safe(
        {
            'window_size': len(items),
            'improved_count': int(direction_counts.get('improved', 0)),
            'worsened_count': int(direction_counts.get('worsened', 0)),
            'unchanged_count': int(direction_counts.get('unchanged', 0)),
            'baseline_count': int(direction_counts.get('baseline', 0)),
            'latest_repair_snapshot': items[0] if items else None,
            'items': items,
        }
    )


class ReconciliationSnapshotService:
    """Captures and reads persisted reconciliation snapshots for admin operations."""

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
            correlation_id=correlation_id or _request_correlation_id(request),
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

    def list(
        self,
        *,
        limit: int = 20,
        source: str = '',
        status: str = '',
        include_report: bool = False,
    ) -> dict[str, Any]:
        limit = max(1, min(int(limit or 20), 250))
        qs = ReconciliationSnapshot.objects.all().order_by('-generated_at', '-created_at')
        if source:
            qs = qs.filter(source=source)
        if status:
            qs = qs.filter(status=status)

        rows = list(qs[:limit])
        all_for_delta = list(qs[: limit + 1])
        previous_by_id: dict[str, ReconciliationSnapshot | None] = {}
        for index, item in enumerate(all_for_delta):
            previous_by_id[str(item.id)] = all_for_delta[index + 1] if index + 1 < len(all_for_delta) else None

        snapshots = [
            _snapshot_to_dict(item, include_report=include_report, previous=previous_by_id.get(str(item.id)))
            for item in rows
        ]
        return _json_safe(
            {
                'status': 'ok',
                'generated_at': timezone.now(),
                'count': len(snapshots),
                'filters': {
                    'limit': limit,
                    'source': source,
                    'status': status,
                    'include_report': include_report,
                },
                'summary': self.summary(),
                'snapshots': snapshots,
            }
        )

    def latest(self, *, source: str = '', status: str = '', include_report: bool = False) -> dict[str, Any]:
        qs = ReconciliationSnapshot.objects.order_by('-generated_at', '-created_at')
        if source:
            qs = qs.filter(source=source)
        if status:
            qs = qs.filter(status=status)

        latest = qs.first()
        previous = qs.exclude(pk=latest.pk).first() if latest else None
        return _json_safe(
            {
                'status': latest.status if latest else 'missing',
                'generated_at': timezone.now(),
                'filters': {'source': source, 'status': status, 'include_report': include_report},
                'summary': self.summary(),
                'snapshot': _snapshot_to_dict(latest, include_report=include_report, previous=previous) if latest else None,
            }
        )

    def summary(self) -> dict[str, Any]:
        latest = ReconciliationSnapshot.objects.order_by('-generated_at', '-created_at').first()
        by_status = list(ReconciliationSnapshot.objects.values('status').annotate(count=Count('id')).order_by('status'))
        by_source = list(ReconciliationSnapshot.objects.values('source').annotate(count=Count('id')).order_by('source'))
        return _json_safe(
            {
                'latest_snapshot_id': str(latest.id) if latest else None,
                'latest_status': latest.status if latest else 'missing',
                'latest_generated_at': latest.generated_at if latest else None,
                'latest_total_issues': latest.total_issues if latest else 0,
                'latest_critical_count': latest.critical_count if latest else 0,
                'snapshot_count': ReconciliationSnapshot.objects.count(),
                'by_status': by_status,
                'by_source': by_source,
            }
        )

    def trend(self, *, limit: int = 30) -> dict[str, Any]:
        limit = max(2, min(int(limit or 30), 250))
        rows = list(ReconciliationSnapshot.objects.order_by('-generated_at', '-created_at')[:limit])
        chronological = list(reversed(rows))
        points = [
            _json_safe(
                {
                    'id': snapshot.id,
                    'status': snapshot.status,
                    'source': snapshot.source,
                    'generated_at': snapshot.generated_at,
                    'total_issues': snapshot.total_issues,
                    'critical_count': snapshot.critical_count,
                    'warning_count': snapshot.warning_count,
                    'info_count': snapshot.info_count,
                    'section_statuses': snapshot.section_statuses or {},
                }
            )
            for snapshot in chronological
        ]
        latest = rows[0] if rows else None
        previous = rows[1] if len(rows) > 1 else None
        return _json_safe(
            {
                'status': latest.status if latest else 'missing',
                'generated_at': timezone.now(),
                'summary': self.summary(),
                'delta': _delta(latest, previous) if latest else {},
                'points': points,
            }
        )


    def metrics(
        self,
        *,
        limit: int = 30,
        source: str = '',
        status: str = '',
    ) -> dict[str, Any]:
        limit = max(2, min(int(limit or 30), 250))
        qs = ReconciliationSnapshot.objects.order_by('-generated_at', '-created_at')
        if source:
            qs = qs.filter(source=source)
        if status:
            qs = qs.filter(status=status)

        rows = list(qs[:limit])
        latest = rows[0] if rows else None
        previous = rows[1] if len(rows) > 1 else None
        latest_delta = _delta(latest, previous) if latest else {}

        return _json_safe(
            {
                'status': latest.status if latest else 'missing',
                'generated_at': timezone.now(),
                'filters': {
                    'limit': limit,
                    'source': source,
                    'status': status,
                },
                'headline': {
                    'snapshot_count': qs.count(),
                    'latest_snapshot_id': str(latest.id) if latest else None,
                    'latest_snapshot_href': _snapshot_href(latest.id) if latest else None,
                    'latest_generated_at': latest.generated_at if latest else None,
                    'latest_status': latest.status if latest else 'missing',
                    'latest_source': latest.source if latest else '',
                    'current_total_issues': int(latest.total_issues or 0) if latest else 0,
                    'current_critical_count': int(latest.critical_count or 0) if latest else 0,
                    'current_warning_count': int(latest.warning_count or 0) if latest else 0,
                    'current_info_count': int(latest.info_count or 0) if latest else 0,
                    'previous_snapshot_id': str(previous.id) if previous else None,
                    'previous_total_issues': int(previous.total_issues or 0) if previous else None,
                    'total_issues_delta': latest_delta.get('total_issues_delta'),
                    'critical_count_delta': latest_delta.get('critical_count_delta'),
                    'warning_count_delta': latest_delta.get('warning_count_delta'),
                    'info_count_delta': latest_delta.get('info_count_delta'),
                    'direction': latest_delta.get('direction', 'missing'),
                },
                'latest': _snapshot_to_dict(latest, previous=previous) if latest else None,
                'distribution': {
                    'by_status': list(qs.values('status').annotate(count=Count('id')).order_by('status')),
                    'by_source': list(qs.values('source').annotate(count=Count('id')).order_by('source')),
                    'window_issue_totals': _window_issue_totals(rows),
                },
                'section_metrics': _latest_section_metrics(current=latest, previous=previous),
                'repair_effectiveness': _repair_effectiveness_metrics(status=status),
                'trend': {
                    'points': _trend_metric_points(rows),
                    'limit': limit,
                    'count': len(rows),
                },
            }
        )

    def compare(
        self,
        *,
        baseline_id: str = '',
        current_id: str = '',
        source: str = '',
        include_report: bool = False,
        diff_limit: int = 100,
    ) -> dict[str, Any]:
        qs = ReconciliationSnapshot.objects.order_by('-generated_at', '-created_at')
        if source:
            qs = qs.filter(source=source)

        current = qs.filter(pk=current_id).first() if current_id else qs.first()
        if current is None:
            return _json_safe(
                {
                    'status': 'missing',
                    'generated_at': timezone.now(),
                    'has_baseline': False,
                    'filters': {
                        'baseline_id': baseline_id,
                        'current_id': current_id,
                        'source': source,
                        'include_report': include_report,
                        'diff_limit': diff_limit,
                    },
                    'detail': 'No reconciliation snapshots were found for comparison.',
                    'baseline_snapshot': None,
                    'current_snapshot': None,
                    'delta': {},
                    'section_diffs': [],
                    'issue_diffs': {
                        'resolved_count': 0,
                        'introduced_count': 0,
                        'persisted_count': 0,
                        'severity_changed_count': 0,
                        'resolved': [],
                        'introduced': [],
                        'persisted': [],
                        'severity_changed': [],
                        'truncated': False,
                        'limit': diff_limit,
                    },
                }
            )

        if baseline_id:
            baseline = qs.filter(pk=baseline_id).exclude(pk=current.pk).first()
        else:
            baseline = qs.exclude(pk=current.pk).filter(generated_at__lte=current.generated_at).first()
            if baseline is None:
                baseline = qs.exclude(pk=current.pk).first()

        payload = _compare_snapshot_payload(
            current=current,
            baseline=baseline,
            include_report=include_report,
            diff_limit=diff_limit,
        )
        payload['filters'] = {
            'baseline_id': baseline_id,
            'current_id': current_id,
            'source': source,
            'include_report': include_report,
            'diff_limit': diff_limit,
        }
        return _json_safe(payload)




def _coerce_min_age_minutes(value: int | str | None, *, default: int = 60) -> int:
    try:
        minutes = int(value if value is not None else default)
    except (TypeError, ValueError):
        minutes = default
    return max(1, min(minutes, 10_080))


def _normalize_snapshot_source(source: str | None, *, default: str = ReconciliationSnapshot.Source.SCHEDULED) -> str:
    value = str(source or '').strip() or default
    if value not in ReconciliationSnapshot.Source.values:
        return default
    return value


def _latest_snapshot_for_source(source: str) -> ReconciliationSnapshot | None:
    return (
        ReconciliationSnapshot.objects.filter(source=source)
        .order_by('-generated_at', '-created_at')
        .first()
    )


def get_reconciliation_snapshot_schedule_status(
    *,
    source: str = ReconciliationSnapshot.Source.SCHEDULED,
    min_age_minutes: int = 60,
) -> dict[str, Any]:
    """Return whether a scheduled reconciliation snapshot is currently due."""
    source = _normalize_snapshot_source(source)
    min_age_minutes = _coerce_min_age_minutes(min_age_minutes)
    now = timezone.now()
    latest_for_source = _latest_snapshot_for_source(source)
    latest_any = ReconciliationSnapshot.objects.order_by('-generated_at', '-created_at').first()

    if latest_for_source is None or latest_for_source.generated_at is None:
        is_due = True
        next_due_at = now
        age_seconds = None
    else:
        due_after = latest_for_source.generated_at + timedelta(minutes=min_age_minutes)
        is_due = due_after <= now
        next_due_at = now if is_due else due_after
        age_seconds = int(max(0, (now - latest_for_source.generated_at).total_seconds()))

    return _json_safe(
        {
            'status': 'due' if is_due else 'fresh',
            'generated_at': now,
            'source': source,
            'min_age_minutes': min_age_minutes,
            'is_due': is_due,
            'latest_snapshot': _snapshot_to_dict(latest_for_source) if latest_for_source else None,
            'latest_any_snapshot': _snapshot_to_dict(latest_any) if latest_any else None,
            'latest_snapshot_age_seconds': age_seconds,
            'next_due_at': next_due_at,
        }
    )


def capture_reconciliation_snapshot_if_due(
    *,
    limit: int = ReconciliationSnapshotService.DEFAULT_LIMIT,
    source: str = ReconciliationSnapshot.Source.SCHEDULED,
    min_age_minutes: int = 60,
    force: bool = False,
    correlation_id: str = '',
    actor=None,
    request=None,
) -> dict[str, Any]:
    """Capture a scheduled snapshot only when the latest source snapshot is stale enough."""
    source = _normalize_snapshot_source(source)
    min_age_minutes = _coerce_min_age_minutes(min_age_minutes)
    schedule_status = get_reconciliation_snapshot_schedule_status(
        source=source,
        min_age_minutes=min_age_minutes,
    )

    if not force and not schedule_status['is_due']:
        return _json_safe(
            {
                'status': 'skipped',
                'captured': False,
                'reason': 'snapshot_not_due',
                'source': source,
                'min_age_minutes': min_age_minutes,
                'latest_snapshot': schedule_status.get('latest_snapshot'),
                'next_due_at': schedule_status.get('next_due_at'),
                'schedule': schedule_status,
            }
        )

    snapshot_payload = capture_reconciliation_snapshot(
        limit=limit,
        source=source,
        correlation_id=correlation_id or f'{source}:scheduled_capture:{timezone.now().isoformat()}'[:128],
        actor=actor,
        request=request,
    )
    return _json_safe(
        {
            'status': 'captured',
            'captured': True,
            'source': source,
            'min_age_minutes': min_age_minutes,
            'snapshot_id': snapshot_payload.get('id'),
            'snapshot_href': snapshot_payload.get('href'),
            'snapshot_status': snapshot_payload.get('status'),
            'total_issues': snapshot_payload.get('total_issues'),
            'critical_count': snapshot_payload.get('critical_count'),
            'warning_count': snapshot_payload.get('warning_count'),
            'info_count': snapshot_payload.get('info_count'),
            'snapshot': snapshot_payload,
            'schedule': get_reconciliation_snapshot_schedule_status(
                source=source,
                min_age_minutes=min_age_minutes,
            ),
        }
    )



def _coerce_retention_days(value: int | str | None, *, default: int) -> int:
    try:
        days = int(value if value is not None else default)
    except (TypeError, ValueError):
        days = default
    return max(1, min(days, 3650))


def _coerce_positive_int(value: int | str | None, *, default: int, minimum: int = 1, maximum: int = 5000) -> int:
    try:
        number = int(value if value is not None else default)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(number, maximum))


def _retention_sources(source: str = '') -> list[str]:
    if source and source in ReconciliationSnapshot.Source.values:
        return [source]
    return list(ReconciliationSnapshot.Source.values)


def _retention_days_by_source(
    *,
    scheduled_days: int = 45,
    repair_days: int = 180,
    manual_days: int = 365,
    ci_days: int = 14,
) -> dict[str, int]:
    return {
        ReconciliationSnapshot.Source.SCHEDULED: _coerce_retention_days(scheduled_days, default=45),
        ReconciliationSnapshot.Source.REPAIR: _coerce_retention_days(repair_days, default=180),
        ReconciliationSnapshot.Source.MANUAL: _coerce_retention_days(manual_days, default=365),
        ReconciliationSnapshot.Source.CI: _coerce_retention_days(ci_days, default=14),
    }


def _snapshot_retention_candidate(snapshot: ReconciliationSnapshot, *, now=None, reason: str = 'expired') -> dict[str, Any]:
    now = now or timezone.now()
    age_seconds = None
    age_days = None
    if snapshot.generated_at:
        age_seconds = int(max(0, (now - snapshot.generated_at).total_seconds()))
        age_days = age_seconds // 86400
    return _json_safe(
        {
            'id': snapshot.id,
            'href': _snapshot_href(snapshot.id),
            'status': snapshot.status,
            'source': snapshot.source,
            'generated_at': snapshot.generated_at,
            'created_at': snapshot.created_at,
            'correlation_id': snapshot.correlation_id,
            'total_issues': snapshot.total_issues,
            'critical_count': snapshot.critical_count,
            'warning_count': snapshot.warning_count,
            'info_count': snapshot.info_count,
            'age_seconds': age_seconds,
            'age_days': age_days,
            'prune_reason': reason,
        }
    )


def _protected_retention_snapshot_ids(*, sources: list[str], keep_min_per_source: int) -> set[str]:
    protected_ids: set[str] = set()
    for source in sources:
        ids = list(
            ReconciliationSnapshot.objects.filter(source=source)
            .order_by('-generated_at', '-created_at')
            .values_list('id', flat=True)[:keep_min_per_source]
        )
        protected_ids.update(str(item) for item in ids)
    return protected_ids


def _retention_policy_payload(
    *,
    source: str,
    scheduled_days: int,
    repair_days: int,
    manual_days: int,
    ci_days: int,
    keep_min_per_source: int,
    max_candidates: int,
    include_candidates: bool,
    dry_run: bool,
) -> dict[str, Any]:
    days_by_source = _retention_days_by_source(
        scheduled_days=scheduled_days,
        repair_days=repair_days,
        manual_days=manual_days,
        ci_days=ci_days,
    )
    return _json_safe(
        {
            'source': source,
            'sources': _retention_sources(source),
            'days_by_source': days_by_source,
            'keep_min_per_source': keep_min_per_source,
            'max_candidates': max_candidates,
            'include_candidates': include_candidates,
            'dry_run': dry_run,
        }
    )


def _retention_candidate_rows(
    *,
    source: str = '',
    scheduled_days: int = 45,
    repair_days: int = 180,
    manual_days: int = 365,
    ci_days: int = 14,
    keep_min_per_source: int = 25,
    max_candidates: int = 500,
    now=None,
) -> tuple[list[ReconciliationSnapshot], int, dict[str, Any]]:
    now = now or timezone.now()
    source = source if source in ReconciliationSnapshot.Source.values else ''
    keep_min_per_source = _coerce_positive_int(keep_min_per_source, default=25, maximum=500)
    max_candidates = _coerce_positive_int(max_candidates, default=500, maximum=5000)
    days_by_source = _retention_days_by_source(
        scheduled_days=scheduled_days,
        repair_days=repair_days,
        manual_days=manual_days,
        ci_days=ci_days,
    )
    sources = _retention_sources(source)
    protected_ids = _protected_retention_snapshot_ids(sources=sources, keep_min_per_source=keep_min_per_source)
    candidates: list[ReconciliationSnapshot] = []
    total_candidate_count = 0
    by_source: dict[str, dict[str, Any]] = {}

    for current_source in sources:
        cutoff = now - timedelta(days=days_by_source[current_source])
        qs = (
            ReconciliationSnapshot.objects.filter(source=current_source, generated_at__lt=cutoff)
            .exclude(pk__in=protected_ids)
            .order_by('generated_at', 'created_at')
        )
        source_count = int(qs.count())
        total_candidate_count += source_count
        by_source[current_source] = {
            'retention_days': days_by_source[current_source],
            'cutoff': cutoff,
            'candidate_count': source_count,
            'protected_count': ReconciliationSnapshot.objects.filter(source=current_source, pk__in=protected_ids).count(),
        }
        remaining_slots = max_candidates - len(candidates)
        if remaining_slots > 0:
            candidates.extend(list(qs[:remaining_slots]))

    candidates.sort(key=lambda item: (item.generated_at, item.created_at))
    return candidates[:max_candidates], total_candidate_count, _json_safe(
        {
            'by_source': by_source,
            'protected_ids': list(sorted(protected_ids)),
            'truncated': total_candidate_count > max_candidates,
        }
    )


def get_reconciliation_snapshot_retention(
    *,
    source: str = '',
    scheduled_days: int = 45,
    repair_days: int = 180,
    manual_days: int = 365,
    ci_days: int = 14,
    keep_min_per_source: int = 25,
    max_candidates: int = 500,
    include_candidates: bool = True,
    dry_run: bool = True,
    execute: bool = False,
) -> dict[str, Any]:
    """Preview or execute reconciliation snapshot retention pruning.

    Retention deliberately keeps a minimum recent history per source so manual/repair snapshots
    used for admin investigations are not removed by an aggressive scheduled cleanup.
    """
    now = timezone.now()
    source = source if source in ReconciliationSnapshot.Source.values else ''
    keep_min_per_source = _coerce_positive_int(keep_min_per_source, default=25, maximum=500)
    max_candidates = _coerce_positive_int(max_candidates, default=500, maximum=5000)
    policy = _retention_policy_payload(
        source=source,
        scheduled_days=scheduled_days,
        repair_days=repair_days,
        manual_days=manual_days,
        ci_days=ci_days,
        keep_min_per_source=keep_min_per_source,
        max_candidates=max_candidates,
        include_candidates=include_candidates,
        dry_run=dry_run,
    )
    rows, total_candidate_count, internals = _retention_candidate_rows(
        source=source,
        scheduled_days=scheduled_days,
        repair_days=repair_days,
        manual_days=manual_days,
        ci_days=ci_days,
        keep_min_per_source=keep_min_per_source,
        max_candidates=max_candidates,
        now=now,
    )
    candidate_ids = [item.pk for item in rows]
    deleted_count = 0
    deleted_ids: list[str] = []
    action = 'preview'

    if execute and not dry_run:
        action = 'pruned'
        if candidate_ids:
            deleted_ids = [str(item) for item in candidate_ids]
            deleted_count = len(deleted_ids)
            ReconciliationSnapshot.objects.filter(pk__in=candidate_ids).delete()
    elif execute and dry_run:
        action = 'dry_run'

    payload = {
        'status': action,
        'generated_at': now,
        'policy': policy,
        'summary': {
            'snapshot_count': ReconciliationSnapshot.objects.count(),
            'candidate_count': total_candidate_count,
            'returned_candidate_count': len(rows),
            'truncated': bool(internals.get('truncated')),
            'delete_limit': max_candidates,
            'deleted_count': deleted_count,
            'kept_min_per_source': keep_min_per_source,
        },
        'source_breakdown': internals.get('by_source') or {},
        'deleted_ids': deleted_ids,
    }
    if include_candidates:
        payload['candidates'] = [_snapshot_retention_candidate(item, now=now) for item in rows]
    else:
        payload['candidates'] = []
    return _json_safe(payload)


def prune_reconciliation_snapshots(**kwargs) -> dict[str, Any]:
    return get_reconciliation_snapshot_retention(execute=True, **kwargs)


def _repair_snapshot_metric(snapshot_payload: dict[str, Any], key: str) -> int:
    value = snapshot_payload.get(key)
    if value is None:
        value = (snapshot_payload.get('summary') or {}).get(key)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _repair_snapshot_correlation_id(repair_payload: dict[str, Any]) -> str:
    audit_event_id = str(repair_payload.get('audit_event_id') or '')
    action = str(repair_payload.get('action') or 'repair')
    entity_type = str(repair_payload.get('entity_type') or '')
    entity_id = str(repair_payload.get('entity_id') or '')
    if audit_event_id:
        return f'repair:{audit_event_id}'[:128]
    return f'repair:{action}:{entity_type}:{entity_id}'[:128]


def _repair_snapshot_summary(
    *,
    snapshot_payload: dict[str, Any],
    previous: ReconciliationSnapshot | None,
    repair_payload: dict[str, Any],
) -> dict[str, Any]:
    current_problem_count = _repair_snapshot_metric(snapshot_payload, 'total_issues')
    current_critical_count = _repair_snapshot_metric(snapshot_payload, 'critical_count')
    current_warning_count = _repair_snapshot_metric(snapshot_payload, 'warning_count')

    previous_problem_count = int(previous.total_issues) if previous else None
    previous_critical_count = int(previous.critical_count) if previous else None
    previous_warning_count = int(previous.warning_count) if previous else None

    problem_delta = None if previous_problem_count is None else current_problem_count - previous_problem_count
    critical_delta = None if previous_critical_count is None else current_critical_count - previous_critical_count
    warning_delta = None if previous_warning_count is None else current_warning_count - previous_warning_count
    improved = bool(problem_delta is not None and (critical_delta or 0) <= 0 and problem_delta < 0)
    worsened = bool(problem_delta is not None and ((critical_delta or 0) > 0 or problem_delta > 0))

    return _json_safe(
        {
            'status': 'captured',
            'source': ReconciliationSnapshot.Source.REPAIR,
            'snapshot_id': snapshot_payload.get('id'),
            'href': snapshot_payload.get('href'),
            'generated_at': snapshot_payload.get('generated_at'),
            'snapshot_status': snapshot_payload.get('status'),
            'has_previous': previous is not None,
            'previous_snapshot_id': str(previous.id) if previous else None,
            'previous_problem_count': previous_problem_count,
            'current_problem_count': current_problem_count,
            'problem_delta': problem_delta,
            'previous_critical_count': previous_critical_count,
            'current_critical_count': current_critical_count,
            'critical_delta': critical_delta,
            'previous_warning_count': previous_warning_count,
            'current_warning_count': current_warning_count,
            'warning_delta': warning_delta,
            'improved': improved,
            'worsened': worsened,
            'repair': {
                'action': repair_payload.get('action'),
                'status': repair_payload.get('status'),
                'changed': repair_payload.get('changed'),
                'entity_type': repair_payload.get('entity_type'),
                'entity_id': repair_payload.get('entity_id'),
                'audit_event_id': repair_payload.get('audit_event_id'),
            },
            'snapshot': snapshot_payload,
        }
    )


def capture_repair_reconciliation_snapshot(
    *,
    repair_payload: dict[str, Any],
    request=None,
    limit: int = ReconciliationSnapshotService.DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Capture source=repair snapshot after a completed repair action and compare it with the previous snapshot."""
    previous = ReconciliationSnapshot.objects.order_by('-generated_at', '-created_at').first()
    snapshot_payload = capture_reconciliation_snapshot(
        limit=limit,
        source=ReconciliationSnapshot.Source.REPAIR,
        correlation_id=_repair_snapshot_correlation_id(repair_payload),
        request=request,
    )
    return _repair_snapshot_summary(
        snapshot_payload=snapshot_payload,
        previous=previous,
        repair_payload=repair_payload,
    )


def _coerce_alert_threshold(value: int | str | None, *, default: int, minimum: int = 0, maximum: int = 10_000) -> int:
    try:
        number = int(value if value is not None else default)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(number, maximum))


def _latest_snapshot_for_alert(source: str = '') -> ReconciliationSnapshot | None:
    qs = ReconciliationSnapshot.objects.order_by('-generated_at', '-created_at')
    if source:
        qs = qs.filter(source=source)
    return qs.first()


def _previous_snapshot_for_alert(snapshot: ReconciliationSnapshot | None, *, source: str = '') -> ReconciliationSnapshot | None:
    if snapshot is None:
        return None
    qs = ReconciliationSnapshot.objects.exclude(pk=snapshot.pk).order_by('-generated_at', '-created_at')
    if source:
        qs = qs.filter(source=source)
    return qs.filter(generated_at__lte=snapshot.generated_at).first() or qs.first()


def _alert_item(
    *,
    code: str,
    severity: str,
    title: str,
    message: str,
    snapshot: ReconciliationSnapshot | None,
    previous: ReconciliationSnapshot | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _json_safe(
        {
            'code': code,
            'severity': severity,
            'title': title,
            'message': message,
            'snapshot_id': str(snapshot.id) if snapshot else None,
            'snapshot_href': _snapshot_href(snapshot.id) if snapshot else None,
            'snapshot_source': snapshot.source if snapshot else '',
            'snapshot_status': snapshot.status if snapshot else 'missing',
            'snapshot_generated_at': snapshot.generated_at if snapshot else None,
            'previous_snapshot_id': str(previous.id) if previous else None,
            'previous_snapshot_href': _snapshot_href(previous.id) if previous else None,
            'evidence': evidence or {},
        }
    )


def evaluate_reconciliation_snapshot_alerts(
    *,
    source: str = '',
    min_total_delta: int = 1,
    min_critical_delta: int = 1,
    stale_after_minutes: int = 180,
) -> dict[str, Any]:
    """Evaluate current reconciliation snapshot health without creating side effects."""
    source = source if source in ReconciliationSnapshot.Source.values else ''
    min_total_delta = _coerce_alert_threshold(min_total_delta, default=1)
    min_critical_delta = _coerce_alert_threshold(min_critical_delta, default=1)
    stale_after_minutes = _coerce_alert_threshold(stale_after_minutes, default=180, minimum=1, maximum=43_200)

    latest = _latest_snapshot_for_alert(source=source)
    previous = _previous_snapshot_for_alert(latest, source=source)
    now = timezone.now()
    alerts: list[dict[str, Any]] = []

    if latest is None:
        alerts.append(
            _alert_item(
                code='reconciliation_snapshot_missing',
                severity='warning',
                title='No reconciliation snapshots captured',
                message='No persisted reconciliation snapshot exists for the requested filter.',
                snapshot=None,
                evidence={'source': source or 'any'},
            )
        )
        return _json_safe(
            {
                'status': 'warning',
                'generated_at': now,
                'has_alerts': True,
                'filters': {
                    'source': source,
                    'min_total_delta': min_total_delta,
                    'min_critical_delta': min_critical_delta,
                    'stale_after_minutes': stale_after_minutes,
                },
                'latest_snapshot': None,
                'previous_snapshot': None,
                'delta': {},
                'alerts': alerts,
                'alert_count': len(alerts),
            }
        )

    delta = _delta(latest, previous)
    total_delta = int(delta.get('total_issues_delta') or 0)
    critical_delta = int(delta.get('critical_count_delta') or 0)
    age_minutes = int(max(0, (now - latest.generated_at).total_seconds() // 60)) if latest.generated_at else None

    if latest.status == ReconciliationSnapshot.Status.CRITICAL:
        alerts.append(
            _alert_item(
                code='reconciliation_snapshot_critical',
                severity='critical',
                title='Reconciliation snapshot is critical',
                message='The latest reconciliation snapshot is critical and requires operator attention.',
                snapshot=latest,
                previous=previous,
                evidence={
                    'total_issues': int(latest.total_issues or 0),
                    'critical_count': int(latest.critical_count or 0),
                    'source': latest.source,
                },
            )
        )
    elif latest.status == ReconciliationSnapshot.Status.DEGRADED:
        alerts.append(
            _alert_item(
                code='reconciliation_snapshot_degraded',
                severity='warning',
                title='Reconciliation snapshot is degraded',
                message='The latest reconciliation snapshot has unresolved drift.',
                snapshot=latest,
                previous=previous,
                evidence={
                    'total_issues': int(latest.total_issues or 0),
                    'critical_count': int(latest.critical_count or 0),
                    'source': latest.source,
                },
            )
        )

    if previous is not None and critical_delta >= min_critical_delta and critical_delta > 0:
        alerts.append(
            _alert_item(
                code='reconciliation_critical_issues_increased',
                severity='critical',
                title='Critical reconciliation issues increased',
                message='Critical reconciliation issue count increased compared with the previous snapshot.',
                snapshot=latest,
                previous=previous,
                evidence={
                    'previous_critical_count': int(previous.critical_count or 0),
                    'current_critical_count': int(latest.critical_count or 0),
                    'critical_count_delta': critical_delta,
                },
            )
        )

    if previous is not None and total_delta >= min_total_delta and total_delta > 0:
        alerts.append(
            _alert_item(
                code='reconciliation_total_issues_increased',
                severity='warning',
                title='Total reconciliation issues increased',
                message='Total reconciliation issue count increased compared with the previous snapshot.',
                snapshot=latest,
                previous=previous,
                evidence={
                    'previous_total_issues': int(previous.total_issues or 0),
                    'current_total_issues': int(latest.total_issues or 0),
                    'total_issues_delta': total_delta,
                },
            )
        )

    if latest.source == ReconciliationSnapshot.Source.SCHEDULED and age_minutes is not None and age_minutes > stale_after_minutes:
        alerts.append(
            _alert_item(
                code='reconciliation_scheduled_snapshot_stale',
                severity='warning',
                title='Scheduled reconciliation snapshot is stale',
                message='The latest scheduled reconciliation snapshot is older than the configured freshness threshold.',
                snapshot=latest,
                previous=previous,
                evidence={
                    'age_minutes': age_minutes,
                    'stale_after_minutes': stale_after_minutes,
                },
            )
        )

    max_severity = 'ok'
    if any(item.get('severity') == 'critical' for item in alerts):
        max_severity = 'critical'
    elif alerts:
        max_severity = 'warning'

    return _json_safe(
        {
            'status': max_severity,
            'generated_at': now,
            'has_alerts': bool(alerts),
            'filters': {
                'source': source,
                'min_total_delta': min_total_delta,
                'min_critical_delta': min_critical_delta,
                'stale_after_minutes': stale_after_minutes,
            },
            'latest_snapshot': _snapshot_to_dict(latest, previous=previous),
            'previous_snapshot': _snapshot_to_dict(previous) if previous else None,
            'delta': delta,
            'alerts': alerts,
            'alert_count': len(alerts),
        }
    )


def _alert_dedupe_key(alert: dict[str, Any]) -> str:
    return ':'.join(
        [
            'reconciliation',
            str(alert.get('code') or 'unknown'),
            str(alert.get('snapshot_id') or 'missing'),
        ]
    )[:255]


def _has_recent_admin_notification(alert_key: str, *, lookback_hours: int = 24) -> bool:
    try:
        from apps.notifications.models import Notification, NotificationType
    except Exception:
        return False

    since = timezone.now() - timedelta(hours=max(1, min(int(lookback_hours or 24), 720)))
    qs = Notification.objects.filter(
        notification_type=NotificationType.SYSTEM,
        created_at__gte=since,
    ).only('metadata')
    for item in qs.iterator(chunk_size=200):
        if (item.metadata or {}).get('alert_key') == alert_key:
            return True
    return False


def _notify_admins_about_alert(alert: dict[str, Any], *, alert_key: str, lookback_hours: int = 24) -> int:
    try:
        from django.contrib.auth import get_user_model
        from django.db.models import Q

        from apps.notifications.models import DeliveryStatus, Notification, NotificationChannel, NotificationType
    except Exception:
        return 0

    if _has_recent_admin_notification(alert_key, lookback_hours=lookback_hours):
        return 0

    User = get_user_model()
    users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True), is_active=True).order_by('id')[:100]
    created = 0
    for user in users:
        Notification.objects.create(
            user=user,
            notification_type=NotificationType.SYSTEM,
            channel=NotificationChannel.IN_APP,
            title=str(alert.get('title') or 'Reconciliation alert')[:255],
            body=str(alert.get('message') or 'Reconciliation requires admin attention.'),
            cta_label='Open reconciliation dashboard',
            cta_url='/admin/reconciliation/snapshots',
            metadata={
                'alert_key': alert_key,
                'alert': alert,
                'source': 'ops.reconciliation',
            },
            status=DeliveryStatus.SENT,
            sent_at=timezone.now(),
        )
        created += 1
    return created


def _audit_reconciliation_alert(alert: dict[str, Any], *, alert_key: str, request=None) -> str:
    try:
        from apps.audit.services import AuditService

        audit_event = AuditService.log_admin_action(
            request=request,
            action='reconciliation.snapshot.alert',
            target_type='reconciliation_snapshot',
            target_id=str(alert.get('snapshot_id') or 'missing'),
            reason=str(alert.get('code') or 'reconciliation_alert'),
            status=str(alert.get('severity') or 'warning'),
            context={'alert_key': alert_key, 'alert': alert},
        )
        return str(audit_event.id)
    except Exception:
        return ''


def emit_reconciliation_snapshot_alerts(
    *,
    source: str = '',
    min_total_delta: int = 1,
    min_critical_delta: int = 1,
    stale_after_minutes: int = 180,
    notify_admins: bool = True,
    dedupe_hours: int = 24,
    request=None,
) -> dict[str, Any]:
    """Evaluate and persist reconciliation alerts through audit log and optional admin notifications."""
    evaluation = evaluate_reconciliation_snapshot_alerts(
        source=source,
        min_total_delta=min_total_delta,
        min_critical_delta=min_critical_delta,
        stale_after_minutes=stale_after_minutes,
    )
    emitted: list[dict[str, Any]] = []
    notification_count = 0

    for alert in evaluation.get('alerts') or []:
        alert_key = _alert_dedupe_key(alert)
        audit_event_id = _audit_reconciliation_alert(alert, alert_key=alert_key, request=request)
        created_notifications = 0
        if notify_admins:
            created_notifications = _notify_admins_about_alert(
                alert,
                alert_key=alert_key,
                lookback_hours=dedupe_hours,
            )
        notification_count += created_notifications
        emitted.append(
            _json_safe(
                {
                    'alert_key': alert_key,
                    'code': alert.get('code'),
                    'severity': alert.get('severity'),
                    'audit_event_id': audit_event_id,
                    'notifications_created': created_notifications,
                }
            )
        )

    payload = dict(evaluation)
    payload['emitted'] = emitted
    payload['emitted_count'] = len(emitted)
    payload['notifications_created'] = notification_count
    return _json_safe(payload)


def emit_reconciliation_snapshot_capture_failure_alert(
    *,
    error_message: str,
    source: str = ReconciliationSnapshot.Source.SCHEDULED,
    correlation_id: str = '',
    notify_admins: bool = True,
    request=None,
) -> dict[str, Any]:
    """Persist an alert when scheduled reconciliation snapshot capture itself fails."""
    alert = _alert_item(
        code='reconciliation_snapshot_capture_failed',
        severity='critical',
        title='Reconciliation snapshot capture failed',
        message='Scheduled reconciliation snapshot capture failed before a snapshot could be persisted.',
        snapshot=None,
        evidence={
            'source': source,
            'correlation_id': correlation_id,
            'error_message': str(error_message)[:1000],
        },
    )
    alert_key = ':'.join(['reconciliation', alert['code'], source, correlation_id or timezone.now().date().isoformat()])[:255]
    audit_event_id = _audit_reconciliation_alert(alert, alert_key=alert_key, request=request)
    notifications_created = _notify_admins_about_alert(alert, alert_key=alert_key) if notify_admins else 0
    return _json_safe(
        {
            'status': 'critical',
            'generated_at': timezone.now(),
            'has_alerts': True,
            'alert_count': 1,
            'alerts': [alert],
            'emitted': [
                {
                    'alert_key': alert_key,
                    'code': alert.get('code'),
                    'severity': alert.get('severity'),
                    'audit_event_id': audit_event_id,
                    'notifications_created': notifications_created,
                }
            ],
            'emitted_count': 1,
            'notifications_created': notifications_created,
        }
    )


# v8.38 issue registry -------------------------------------------------------

ISSUE_REPAIR_ACTION_REGISTRY: dict[str, dict[str, str]] = {
    'outbox_delivery_problem': {
        'action': 'retry_outbox',
        'target_entity_type': 'outbox_message',
        'reason': 'Retry failed/dead/stuck outbox message from reconciliation issue registry.',
    },
    'payment_webhook_problem': {
        'action': 'reprocess_webhook',
        'target_entity_type': 'payment_webhook',
        'reason': 'Reprocess failed/rejected/stuck payment webhook from reconciliation issue registry.',
    },
    'completed_order_without_active_entitlement': {
        'action': 'grant_order_access',
        'target_entity_type': 'order',
        'reason': 'Grant missing access for completed order from reconciliation issue registry.',
    },
    'active_entitlement_from_unpaid_order': {
        'action': 'revoke_entitlement',
        'target_entity_type': 'entitlement',
        'reason': 'Revoke active entitlement backed by unpaid order from reconciliation issue registry.',
    },
    'active_entitlement_from_inactive_subscription': {
        'action': 'revoke_entitlement',
        'target_entity_type': 'entitlement',
        'reason': 'Revoke active entitlement backed by inactive subscription from reconciliation issue registry.',
    },
    'succeeded_payment_without_payout_accrual': {
        'action': 'project_payout_accrual',
        'target_entity_type': 'payment',
        'reason': 'Project missing payout accrual from reconciliation issue registry.',
    },
    'payout_accrual_for_non_success_payment': {
        'action': 'reverse_payout_accrual',
        'target_entity_type': 'payout_ledger',
        'reason': 'Reverse payout accrual for non-success payment from reconciliation issue registry.',
    },
}

ISSUE_SEVERITIES = {'critical', 'warning', 'info'}


def _slug(value: Any, *, fallback: str = 'unknown') -> str:
    raw = str(value or '').strip().lower()
    if not raw:
        raw = fallback
    chars: list[str] = []
    last_was_sep = False
    for char in raw:
        if char.isalnum():
            chars.append(char)
            last_was_sep = False
        else:
            if not last_was_sep:
                chars.append('_')
            last_was_sep = True
    normalized = ''.join(chars).strip('_')
    return normalized or fallback


def _normalized_issue_code(issue: dict[str, Any]) -> str:
    return _slug(
        issue.get('issue_code')
        or issue.get('code')
        or issue.get('type')
        or issue.get('kind')
        or issue.get('check_code')
        or 'unknown_issue',
        fallback='unknown_issue',
    )


def _normalized_issue_severity(issue: dict[str, Any]) -> str:
    severity = _slug(issue.get('severity') or issue.get('level') or 'info', fallback='info')
    return severity if severity in ISSUE_SEVERITIES else 'info'


def _normalized_issue_entity(issue: dict[str, Any]) -> tuple[str, str]:
    entity = issue.get('entity') if isinstance(issue.get('entity'), dict) else {}
    entity_type = issue.get('entity_type') or issue.get('entityType') or entity.get('type') or entity.get('entity_type') or 'unknown'
    entity_id = issue.get('entity_id') or issue.get('entityId') or entity.get('id') or entity.get('entity_id') or ''
    return str(entity_type or 'unknown'), str(entity_id or '')


def _issue_related_entities(issue: dict[str, Any]) -> list[dict[str, str]]:
    related = issue.get('related') or []
    result: list[dict[str, str]] = []
    for item in related:
        if not isinstance(item, dict):
            continue
        related_type = str(item.get('entity_type') or item.get('type') or '')
        related_id = str(item.get('entity_id') or item.get('id') or '')
        if not related_type or not related_id:
            continue
        result.append(
            {
                'entity_type': related_type,
                'entity_id': related_id,
                'label': str(item.get('label') or related_type),
                'href': str(item.get('href') or f'/admin/entities/{related_type}/{related_id}'),
            }
        )
    return result


def _repair_target_for_issue(issue: dict[str, Any], *, target_entity_type: str) -> tuple[str, str] | None:
    entity_type, entity_id = _normalized_issue_entity(issue)
    if entity_type == target_entity_type and entity_id:
        return entity_type, entity_id
    for item in _issue_related_entities(issue):
        if item['entity_type'] == target_entity_type and item['entity_id']:
            return item['entity_type'], item['entity_id']
    return None


def _repair_metadata_for_issue(issue: dict[str, Any]) -> dict[str, Any]:
    issue_code = _normalized_issue_code(issue)
    mapping = ISSUE_REPAIR_ACTION_REGISTRY.get(issue_code)
    if not mapping:
        return {
            'repairable': False,
            'repair_action': '',
            'repair_entity_type': '',
            'repair_entity_id': '',
            'repair_reason': '',
            'repair_endpoint': '',
            'repair_policy_href': '',
        }

    target = _repair_target_for_issue(issue, target_entity_type=mapping['target_entity_type'])
    if target is None:
        return {
            'repairable': False,
            'repair_action': mapping['action'],
            'repair_entity_type': mapping['target_entity_type'],
            'repair_entity_id': '',
            'repair_reason': mapping['reason'],
            'repair_endpoint': '/api/v1/ops/admin/reconciliation-repair/',
            'repair_policy_href': '',
        }

    repair_entity_type, repair_entity_id = target
    action = mapping['action']
    return {
        'repairable': True,
        'repair_action': action,
        'repair_entity_type': repair_entity_type,
        'repair_entity_id': repair_entity_id,
        'repair_reason': mapping['reason'],
        'repair_endpoint': '/api/v1/ops/admin/reconciliation-repair/',
        'repair_policy_href': (
            '/api/v1/ops/admin/reconciliation-repair/policy/'
            f'?action={action}&entity_type={repair_entity_type}&entity_id={repair_entity_id}'
        ),
    }


def _issue_identity(issue: dict[str, Any]) -> str:
    entity_type, entity_id = _normalized_issue_entity(issue)
    return ':'.join([_normalized_issue_code(issue), entity_type, entity_id])


def _issue_summary(issue: dict[str, Any]) -> dict[str, Any]:
    entity_type, entity_id = _normalized_issue_entity(issue)
    payload = {
        'identity': _issue_identity(issue),
        'issue_code': _normalized_issue_code(issue),
        'code': _normalized_issue_code(issue),
        'severity': _normalized_issue_severity(issue),
        'section': issue.get('section') or 'unknown',
        'entity_type': entity_type,
        'entity_id': entity_id,
        'entity_href': f'/admin/entities/{entity_type}/{entity_id}' if entity_type and entity_id else '',
        'message': issue.get('message') or issue.get('detail') or '',
        'suggested_action': issue.get('suggested_action') or issue.get('recommended_action') or '',
        'recommended_action': issue.get('recommended_action') or issue.get('suggested_action') or '',
        'related': _issue_related_entities(issue),
        'evidence': issue.get('evidence') or {},
        **_repair_metadata_for_issue(issue),
    }
    return _json_safe(payload)


def _normalized_snapshot_issue(
    *,
    snapshot: ReconciliationSnapshot,
    section_key: str,
    issue: dict[str, Any],
) -> dict[str, Any]:
    item = dict(issue)
    item.setdefault('section', section_key)
    summary = _issue_summary(item)
    summary.update(
        {
            'snapshot_id': str(snapshot.id),
            'snapshot_href': _snapshot_href(snapshot.id),
            'snapshot_source': snapshot.source,
            'snapshot_status': snapshot.status,
            'snapshot_generated_at': snapshot.generated_at,
        }
    )
    return _json_safe(summary)


def _normalized_snapshot_issues(snapshot: ReconciliationSnapshot | None) -> list[dict[str, Any]]:
    if snapshot is None:
        return []
    report = snapshot.report or {}
    sections = report.get('sections') or {}
    result: list[dict[str, Any]] = []
    for section_key, section in sections.items():
        for issue in (section or {}).get('issues') or []:
            if isinstance(issue, dict):
                result.append(_normalized_snapshot_issue(snapshot=snapshot, section_key=str(section_key), issue=issue))
    return result


def _issue_registry_matches(
    issue: dict[str, Any],
    *,
    issue_code: str = '',
    severity: str = '',
    entity_type: str = '',
    entity_id: str = '',
    section: str = '',
    repairable: str | bool | None = '',
) -> bool:
    if issue_code and issue['issue_code'] != _slug(issue_code, fallback=''):
        return False
    if severity and issue['severity'] != severity:
        return False
    if entity_type and issue['entity_type'] != entity_type:
        return False
    if entity_id and issue['entity_id'] != str(entity_id):
        return False
    if section and issue['section'] != section:
        return False
    if repairable not in {'', None}:
        requested = repairable
        if isinstance(requested, str):
            requested = requested.lower() in {'1', 'true', 'yes'}
        if bool(issue.get('repairable')) is not bool(requested):
            return False
    return True


def _issue_registry_counts(issues: list[dict[str, Any]]) -> dict[str, Any]:
    by_severity: dict[str, int] = defaultdict(int)
    by_section: dict[str, int] = defaultdict(int)
    by_issue_code: dict[str, dict[str, Any]] = {}
    by_repair_action: dict[str, int] = defaultdict(int)

    for issue in issues:
        by_severity[issue['severity']] += 1
        by_section[issue['section']] += 1
        bucket = by_issue_code.setdefault(
            issue['issue_code'],
            {
                'issue_code': issue['issue_code'],
                'count': 0,
                'critical_count': 0,
                'warning_count': 0,
                'info_count': 0,
                'repairable_count': 0,
                'sections': set(),
                'entity_types': set(),
            },
        )
        bucket['count'] += 1
        bucket[f"{issue['severity']}_count"] += 1
        if issue.get('repairable'):
            bucket['repairable_count'] += 1
            by_repair_action[issue['repair_action']] += 1
        bucket['sections'].add(issue['section'])
        bucket['entity_types'].add(issue['entity_type'])

    catalog: list[dict[str, Any]] = []
    for bucket in by_issue_code.values():
        catalog.append(
            {
                **bucket,
                'sections': sorted(bucket['sections']),
                'entity_types': sorted(bucket['entity_types']),
            }
        )
    catalog.sort(key=lambda item: (-int(item['critical_count']), -int(item['count']), item['issue_code']))

    return _json_safe(
        {
            'total_count': len(issues),
            'critical_count': int(by_severity.get('critical', 0)),
            'warning_count': int(by_severity.get('warning', 0)),
            'info_count': int(by_severity.get('info', 0)),
            'repairable_count': sum(1 for issue in issues if issue.get('repairable')),
            'by_severity': dict(sorted(by_severity.items())),
            'by_section': dict(sorted(by_section.items())),
            'by_repair_action': dict(sorted(by_repair_action.items())),
            'catalog': catalog,
        }
    )


def _issue_registry_snapshot(
    *,
    snapshot_id: str = '',
    source: str = '',
    status: str = '',
) -> ReconciliationSnapshot | None:
    qs = ReconciliationSnapshot.objects.all().order_by('-generated_at', '-created_at')
    if source:
        qs = qs.filter(source=source)
    if status:
        qs = qs.filter(status=status)
    if snapshot_id:
        return qs.filter(pk=snapshot_id).first()
    return qs.first()


def _issue_registry_previous_snapshot(snapshot: ReconciliationSnapshot | None, *, source: str = '', status: str = '') -> ReconciliationSnapshot | None:
    if snapshot is None:
        return None
    qs = ReconciliationSnapshot.objects.exclude(pk=snapshot.pk).filter(generated_at__lte=snapshot.generated_at)
    if source:
        qs = qs.filter(source=source)
    if status:
        qs = qs.filter(status=status)
    previous = qs.order_by('-generated_at', '-created_at').first()
    if previous is not None:
        return previous
    qs = ReconciliationSnapshot.objects.exclude(pk=snapshot.pk)
    if source:
        qs = qs.filter(source=source)
    if status:
        qs = qs.filter(status=status)
    return qs.order_by('-generated_at', '-created_at').first()


def get_reconciliation_issue_registry(
    *,
    snapshot_id: str = '',
    source: str = '',
    status: str = '',
    issue_code: str = '',
    severity: str = '',
    entity_type: str = '',
    entity_id: str = '',
    section: str = '',
    repairable: str | bool | None = '',
    limit: int = 100,
    include_report: bool = False,
) -> dict[str, Any]:
    """Return a normalized issue registry derived from persisted snapshot JSON.

    This is intentionally read-only and schema-free: it does not introduce a new table yet. It turns
    the current snapshot report into stable issue rows that the admin UI can filter and map to repair actions.
    """
    limit = max(1, min(int(limit or 100), 500))
    snapshot = _issue_registry_snapshot(snapshot_id=str(snapshot_id or ''), source=source, status=status)
    if snapshot is None:
        return _json_safe(
            {
                'status': 'missing',
                'generated_at': timezone.now(),
                'filters': {
                    'snapshot_id': str(snapshot_id or ''),
                    'source': source,
                    'status': status,
                    'issue_code': issue_code,
                    'severity': severity,
                    'entity_type': entity_type,
                    'entity_id': entity_id,
                    'section': section,
                    'repairable': repairable,
                    'limit': limit,
                    'include_report': include_report,
                },
                'snapshot': None,
                'previous_snapshot': None,
                'summary': _issue_registry_counts([]),
                'issues': [],
                'truncated': False,
            }
        )

    previous = _issue_registry_previous_snapshot(snapshot, source=source, status=status)
    previous_identities = {issue['identity'] for issue in _normalized_snapshot_issues(previous)}
    normalized = []
    for issue in _normalized_snapshot_issues(snapshot):
        if _issue_registry_matches(
            issue,
            issue_code=issue_code,
            severity=severity,
            entity_type=entity_type,
            entity_id=entity_id,
            section=section,
            repairable=repairable,
        ):
            issue['seen_in_previous_snapshot'] = issue['identity'] in previous_identities
            issue['state'] = 'persisted' if issue['seen_in_previous_snapshot'] else 'introduced'
            normalized.append(issue)

    normalized.sort(
        key=lambda item: (
            {'critical': 0, 'warning': 1, 'info': 2}.get(item['severity'], 3),
            item['section'],
            item['issue_code'],
            item['entity_type'],
            item['entity_id'],
        )
    )
    limited = normalized[:limit]
    payload = {
        'status': snapshot.status,
        'generated_at': timezone.now(),
        'filters': {
            'snapshot_id': str(snapshot_id or ''),
            'source': source,
            'status': status,
            'issue_code': issue_code,
            'severity': severity,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'section': section,
            'repairable': repairable,
            'limit': limit,
            'include_report': include_report,
        },
        'snapshot': _snapshot_to_dict(snapshot, include_report=include_report, previous=previous),
        'previous_snapshot': _snapshot_to_dict(previous) if previous else None,
        'summary': _issue_registry_counts(normalized),
        'issues': limited,
        'truncated': len(normalized) > limit,
    }
    return _json_safe(payload)

def capture_reconciliation_snapshot(**kwargs) -> dict[str, Any]:
    return ReconciliationSnapshotService().capture(**kwargs)


def list_reconciliation_snapshots(**kwargs) -> dict[str, Any]:
    return ReconciliationSnapshotService().list(**kwargs)


def get_latest_reconciliation_snapshot(**kwargs) -> dict[str, Any]:
    return ReconciliationSnapshotService().latest(**kwargs)


def get_reconciliation_snapshot_trend(**kwargs) -> dict[str, Any]:
    return ReconciliationSnapshotService().trend(**kwargs)


def compare_reconciliation_snapshots(**kwargs) -> dict[str, Any]:
    return ReconciliationSnapshotService().compare(**kwargs)


def get_reconciliation_snapshot_metrics(**kwargs) -> dict[str, Any]:
    return ReconciliationSnapshotService().metrics(**kwargs)


def get_reconciliation_snapshot_schedule(**kwargs) -> dict[str, Any]:
    return get_reconciliation_snapshot_schedule_status(**kwargs)


def get_reconciliation_snapshot_retention_policy(**kwargs) -> dict[str, Any]:
    return get_reconciliation_snapshot_retention(**kwargs)


def evaluate_reconciliation_snapshot_alerts_payload(**kwargs) -> dict[str, Any]:
    return evaluate_reconciliation_snapshot_alerts(**kwargs)


def emit_reconciliation_snapshot_alerts_payload(**kwargs) -> dict[str, Any]:
    return emit_reconciliation_snapshot_alerts(**kwargs)


def get_reconciliation_snapshot_alerts(**kwargs) -> dict[str, Any]:
    return evaluate_reconciliation_snapshot_alerts(**kwargs)


def notify_reconciliation_snapshot_alerts(**kwargs) -> dict[str, Any]:
    return emit_reconciliation_snapshot_alerts(**kwargs)
