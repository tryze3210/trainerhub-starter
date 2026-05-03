from __future__ import annotations

import json
from typing import Any

from django.utils import timezone

from apps.audit.models import AuditEvent


class AuditService:
    """Small audit service used by operator/admin actions.

    AuditEvent already exists in the current schema. v8.18 keeps that table and
    standardizes the payload shape instead of adding a new audit model.
    """

    @staticmethod
    def _request_actor(*, actor=None, request=None):
        if actor is not None:
            return actor if getattr(actor, 'is_authenticated', True) else None
        if request is None:
            return None
        user = getattr(request, 'user', None)
        return user if getattr(user, 'is_authenticated', False) else None

    @staticmethod
    def _request_ip(request=None) -> str | None:
        if request is None:
            return None
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip() or None
        return request.META.get('REMOTE_ADDR')

    @staticmethod
    def _request_user_agent(request=None) -> str:
        if request is None:
            return ''
        return request.META.get('HTTP_USER_AGENT', '')

    @staticmethod
    def _correlation_id(request=None) -> str:
        if request is None:
            return ''
        return (
            request.headers.get('X-Correlation-ID')
            or request.headers.get('X-Request-ID')
            or request.META.get('HTTP_X_CORRELATION_ID')
            or request.META.get('HTTP_X_REQUEST_ID')
            or ''
        )

    @staticmethod
    def _json_safe(value: Any) -> Any:
        """Return value as JSON-compatible data without leaking unserializable objects."""
        try:
            return json.loads(json.dumps(value or {}, default=str))
        except (TypeError, ValueError):
            return {'value': str(value)}

    @staticmethod
    def log(*, actor=None, event_type: str, entity_type: str, entity_id: str, context=None, request=None):
        return AuditEvent.objects.create(
            actor=AuditService._request_actor(actor=actor, request=request),
            event_type=event_type[:64],
            entity_type=entity_type[:64],
            entity_id=str(entity_id)[:64],
            context=AuditService._json_safe(context or {}),
            ip_address=AuditService._request_ip(request),
            user_agent=AuditService._request_user_agent(request),
        )

    @staticmethod
    def log_admin_action(
        *,
        action: str,
        target_type: str,
        target_id: str,
        actor=None,
        request=None,
        reason: str = '',
        status: str = 'accepted',
        context: dict[str, Any] | None = None,
    ):
        """Log an admin/operator action using a consistent context envelope."""
        request_context = {}
        if request is not None:
            request_context = {
                'method': getattr(request, 'method', ''),
                'path': getattr(request, 'path', ''),
                'correlation_id': AuditService._correlation_id(request),
            }
        payload = {
            'action': action,
            'target_type': target_type,
            'target_id': str(target_id),
            'reason': reason or '',
            'status': status,
            'request': request_context,
            'context': context or {},
            'recorded_at': timezone.now().isoformat(),
        }
        return AuditService.log(
            actor=actor,
            request=request,
            event_type=f'admin.{action}'[:64],
            entity_type=target_type,
            entity_id=str(target_id),
            context=payload,
        )
