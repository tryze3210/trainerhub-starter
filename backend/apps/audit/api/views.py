from __future__ import annotations

import csv
import json
from datetime import datetime, time, timedelta

from django.db import transaction
from django.db.models import Count, Max, Min, Q, QuerySet
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.api.serializers import AuditEventSerializer
from apps.audit.models import AuditEvent

AUDIT_EXPORT_LIMIT = 10_000
AUDIT_RETENTION_DEFAULT_DAYS = 180
AUDIT_RETENTION_MAX_DAYS = 3650
AUDIT_RETENTION_TOP_EVENT_TYPES = 20
AUDIT_RETENTION_PREVIEW_DEFAULT_BATCH_SIZE = 100
AUDIT_RETENTION_PREVIEW_MAX_BATCH_SIZE = 1000


class AuditAdminViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Admin-only audit feed for operator actions and support investigations."""

    permission_classes = [IsAdminUser]
    serializer_class = AuditEventSerializer

    def get_queryset(self):
        return build_admin_audit_queryset(self.request.query_params, include_limit=True)


class AuditAdminCsvExportView(APIView):
    """Admin-only CSV export for the audit feed with the same filters as list view."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        queryset = build_admin_audit_queryset(request.query_params, include_limit=False)
        total_count = queryset.count()
        rows = list(queryset[:AUDIT_EXPORT_LIMIT])
        truncated = total_count > len(rows)

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="trainerhub-admin-audit-events.csv"'
        response.write('\ufeff')

        writer = csv.writer(response)
        writer.writerow(
            [
                'id',
                'created_at',
                'event_type',
                'entity_type',
                'entity_id',
                'actor_id',
                'actor_email',
                'ip_address',
                'user_agent',
                'context_json',
            ]
        )

        for event in rows:
            writer.writerow(
                [
                    str(event.id),
                    event.created_at.isoformat() if event.created_at else '',
                    event.event_type,
                    event.entity_type,
                    event.entity_id,
                    str(event.actor_id or ''),
                    getattr(event.actor, 'email', '') if event.actor_id else '',
                    event.ip_address or '',
                    event.user_agent or '',
                    json.dumps(event.context or {}, ensure_ascii=False, sort_keys=True),
                ]
            )

        _record_audit_export_event(
            request=request,
            row_count=len(rows),
            total_count=total_count,
            truncated=truncated,
            filters=_active_filter_snapshot(request.query_params),
        )
        return response


class AuditAdminRetentionSummaryView(APIView):
    """Read-only retention summary for planning audit log cleanup policies."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        older_than_days = _parse_retention_days(request.query_params.get('older_than_days'))
        cutoff = timezone.now() - timedelta(days=older_than_days)

        base_queryset = build_admin_audit_queryset(request.query_params, include_limit=False)
        stale_queryset = base_queryset.filter(created_at__lt=cutoff)
        aggregate = stale_queryset.aggregate(oldest_created_at=Min('created_at'), newest_created_at=Max('created_at'))

        by_event_type = list(
            stale_queryset.values('event_type')
            .annotate(count=Count('id'))
            .order_by('-count', 'event_type')[:AUDIT_RETENTION_TOP_EVENT_TYPES]
        )
        by_entity_type = list(
            stale_queryset.values('entity_type')
            .annotate(count=Count('id'))
            .order_by('-count', 'entity_type')[:AUDIT_RETENTION_TOP_EVENT_TYPES]
        )

        return Response(
            {
                'older_than_days': older_than_days,
                'cutoff': cutoff.isoformat(),
                'total_matching_events': base_queryset.count(),
                'stale_events': stale_queryset.count(),
                'oldest_created_at': aggregate['oldest_created_at'].isoformat()
                if aggregate['oldest_created_at']
                else None,
                'newest_created_at': aggregate['newest_created_at'].isoformat()
                if aggregate['newest_created_at']
                else None,
                'filters': _active_filter_snapshot(request.query_params),
                'by_event_type': by_event_type,
                'by_entity_type': by_entity_type,
                'note': 'Read-only summary. No audit events are deleted by this endpoint.',
            }
        )



class AuditAdminRetentionPreviewView(APIView):
    """Read-only retention cleanup preview. It never deletes audit events."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        older_than_days = _parse_retention_days(request.query_params.get('older_than_days'))
        batch_size = _parse_retention_batch_size(request.query_params.get('batch_size'))
        cutoff = timezone.now() - timedelta(days=older_than_days)

        base_queryset = build_admin_audit_queryset(request.query_params, include_limit=False)
        stale_queryset = base_queryset.filter(created_at__lt=cutoff).order_by('created_at', 'id')
        candidates_total = stale_queryset.count()
        preview_events = list(stale_queryset[:batch_size])

        return Response(
            {
                'mode': 'preview',
                'deletion_performed': False,
                'older_than_days': older_than_days,
                'batch_size': batch_size,
                'cutoff': cutoff.isoformat(),
                'total_matching_events': base_queryset.count(),
                'candidates_total': candidates_total,
                'preview_count': len(preview_events),
                'has_more': candidates_total > len(preview_events),
                'filters': _active_filter_snapshot(request.query_params),
                'events': [_serialize_retention_preview_event(event) for event in preview_events],
                'note': 'Read-only cleanup preview. No audit events are deleted by this endpoint.',
            }
        )


class AuditAdminRetentionCleanupView(APIView):
    """Confirmed retention cleanup action for old audit events."""

    permission_classes = [IsAdminUser]

    def post(self, request):
        params = _retention_request_params(request)
        confirm = _parse_confirm(params.get('confirm'))
        older_than_days = _parse_retention_days(params.get('older_than_days'))
        batch_size = _parse_retention_batch_size(params.get('batch_size'))
        cutoff = timezone.now() - timedelta(days=older_than_days)

        if not confirm:
            return Response(
                {
                    'mode': 'cleanup',
                    'deletion_performed': False,
                    'older_than_days': older_than_days,
                    'batch_size': batch_size,
                    'cutoff': cutoff.isoformat(),
                    'deleted_count': 0,
                    'error': 'Confirmation required. Send confirm=true to delete stale audit events.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        base_queryset = build_admin_audit_queryset(params, include_limit=False)
        stale_queryset = base_queryset.filter(created_at__lt=cutoff).order_by('created_at', 'id')
        total_matching_events = base_queryset.count()
        candidates_total = stale_queryset.count()
        candidate_ids = list(stale_queryset.values_list('id', flat=True)[:batch_size])

        with transaction.atomic():
            deleted_count = 0
            if candidate_ids:
                deleted_count, _ = AuditEvent.objects.filter(id__in=candidate_ids).delete()

            cleanup_event = _record_audit_retention_cleanup_event(
                request=request,
                older_than_days=older_than_days,
                batch_size=batch_size,
                cutoff=cutoff,
                total_matching_events=total_matching_events,
                candidates_total=candidates_total,
                deleted_count=deleted_count,
                filters=_active_filter_snapshot(params),
            )

        return Response(
            {
                'mode': 'cleanup',
                'deletion_performed': True,
                'older_than_days': older_than_days,
                'batch_size': batch_size,
                'cutoff': cutoff.isoformat(),
                'total_matching_events': total_matching_events,
                'candidates_total': candidates_total,
                'deleted_count': deleted_count,
                'has_more': candidates_total > deleted_count,
                'filters': _active_filter_snapshot(params),
                'audit_event_id': str(cleanup_event.id),
                'note': 'Confirmed retention cleanup completed. Only events older than cutoff were eligible.',
            }
        )

def build_admin_audit_queryset(params, *, include_limit: bool) -> QuerySet[AuditEvent]:
    queryset = AuditEvent.objects.select_related('actor').all()

    event_type = (params.get('event_type') or '').strip()
    entity_type = (params.get('entity_type') or '').strip()
    entity_id = (params.get('entity_id') or '').strip()
    actor_id = (params.get('actor_id') or '').strip()
    search = (params.get('search') or '').strip()
    created_from = _parse_boundary(params.get('created_from'), end_of_day=False)
    created_to = _parse_boundary(params.get('created_to'), end_of_day=True)
    limit = _parse_limit(params.get('limit'))

    if event_type:
        queryset = queryset.filter(event_type=event_type)
    if entity_type:
        queryset = queryset.filter(entity_type=entity_type)
    if entity_id:
        queryset = queryset.filter(entity_id=entity_id)
    if actor_id:
        queryset = queryset.filter(actor_id=actor_id)
    if created_from:
        queryset = queryset.filter(created_at__gte=created_from)
    if created_to:
        queryset = queryset.filter(created_at__lte=created_to)
    if search:
        queryset = queryset.filter(
            Q(event_type__icontains=search)
            | Q(entity_type__icontains=search)
            | Q(entity_id__icontains=search)
            | Q(actor__email__icontains=search)
            | Q(ip_address__icontains=search)
            | Q(user_agent__icontains=search)
        )

    queryset = queryset.order_by('-created_at', '-id')
    if include_limit and limit:
        return queryset[:limit]
    return queryset



def _retention_request_params(request) -> dict[str, object]:
    params: dict[str, object] = dict(request.query_params.items())
    data = getattr(request, 'data', None)
    if isinstance(data, dict):
        params.update(data)
    return params


def _parse_confirm(value: object) -> bool:
    if isinstance(value, bool):
        return value
    raw = str(value or '').strip().lower()
    return raw in {'1', 'true', 'yes', 'y', 'on'}

def _parse_retention_days(value: str | None) -> int:
    raw = str(value or '').strip()
    if not raw:
        return AUDIT_RETENTION_DEFAULT_DAYS
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return AUDIT_RETENTION_DEFAULT_DAYS
    return max(1, min(parsed, AUDIT_RETENTION_MAX_DAYS))


def _parse_retention_batch_size(value: str | None) -> int:
    raw = str(value or '').strip()
    if not raw:
        return AUDIT_RETENTION_PREVIEW_DEFAULT_BATCH_SIZE
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return AUDIT_RETENTION_PREVIEW_DEFAULT_BATCH_SIZE
    return max(1, min(parsed, AUDIT_RETENTION_PREVIEW_MAX_BATCH_SIZE))


def _serialize_retention_preview_event(event: AuditEvent) -> dict[str, object]:
    return {
        'id': str(event.id),
        'created_at': event.created_at.isoformat() if event.created_at else None,
        'event_type': event.event_type,
        'entity_type': event.entity_type,
        'entity_id': event.entity_id,
        'actor_id': str(event.actor_id or ''),
        'actor_email': getattr(event.actor, 'email', '') if event.actor_id else '',
        'ip_address': event.ip_address or '',
        'user_agent': event.user_agent or '',
    }


def _parse_limit(value: str | None) -> int | None:
    if not value:
        return None

    try:
        return max(1, min(int(str(value).strip()), 500))
    except (TypeError, ValueError):
        return 100


def _parse_boundary(value: str | None, *, end_of_day: bool) -> datetime | None:
    raw = (value or '').strip()
    if not raw:
        return None

    parsed_datetime = parse_datetime(raw)
    if parsed_datetime is not None:
        if timezone.is_naive(parsed_datetime):
            return timezone.make_aware(parsed_datetime, timezone.get_current_timezone())
        return parsed_datetime

    parsed_date = parse_date(raw)
    if parsed_date is None:
        return None

    boundary_time = time.max if end_of_day else time.min
    boundary = datetime.combine(parsed_date, boundary_time)
    return timezone.make_aware(boundary, timezone.get_current_timezone())


def _active_filter_snapshot(params) -> dict[str, str]:
    keys = ['event_type', 'entity_type', 'entity_id', 'actor_id', 'created_from', 'created_to', 'search']
    return {key: str(params.get(key)).strip() for key in keys if (params.get(key) or '').strip()}


def _record_audit_export_event(*, request, row_count: int, total_count: int, truncated: bool, filters: dict[str, str]) -> None:
    user = getattr(request, 'user', None)
    actor = user if getattr(user, 'is_authenticated', False) else None

    AuditEvent.objects.create(
        actor=actor,
        event_type='admin.audit.csv_export',
        entity_type='audit_export',
        entity_id='events',
        context={
            'action': 'admin.audit.csv_export',
            'status': 'succeeded',
            'context': {
                'export_kind': 'audit_events',
                'filename': 'trainerhub-admin-audit-events.csv',
                'row_count': row_count,
                'total_count': total_count,
                'limit': AUDIT_EXPORT_LIMIT,
                'truncated': truncated,
                'filters': filters,
            },
            'request': {
                'method': request.method,
                'path': request.get_full_path(),
                'correlation_id': request.headers.get('X-Request-ID', ''),
            },
        },
        ip_address=_client_ip(request),
        user_agent=request.headers.get('User-Agent', '')[:1024],
    )


def _record_audit_retention_cleanup_event(
    *,
    request,
    older_than_days: int,
    batch_size: int,
    cutoff,
    total_matching_events: int,
    candidates_total: int,
    deleted_count: int,
    filters: dict[str, str],
) -> AuditEvent:
    user = getattr(request, 'user', None)
    actor = user if getattr(user, 'is_authenticated', False) else None

    return AuditEvent.objects.create(
        actor=actor,
        event_type='admin.audit.retention.cleanup',
        entity_type='audit_retention',
        entity_id='cleanup',
        context={
            'action': 'admin.audit.retention.cleanup',
            'status': 'succeeded',
            'context': {
                'older_than_days': older_than_days,
                'batch_size': batch_size,
                'cutoff': cutoff.isoformat(),
                'total_matching_events': total_matching_events,
                'candidates_total': candidates_total,
                'deleted_count': deleted_count,
                'has_more': candidates_total > deleted_count,
                'filters': filters,
            },
            'request': {
                'method': request.method,
                'path': request.get_full_path(),
                'correlation_id': request.headers.get('X-Request-ID', ''),
            },
        },
        ip_address=_client_ip(request),
        user_agent=request.headers.get('User-Agent', '')[:1024],
    )


def _client_ip(request) -> str | None:
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip() or None
    return request.META.get('REMOTE_ADDR') or None
