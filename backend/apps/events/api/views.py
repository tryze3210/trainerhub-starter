from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import AuditService
from apps.events.api.serializers import (
    DispatchOutboxSerializer,
    DomainEventSerializer,
    EmitEventSerializer,
    EventHandlerSerializer,
    InboxMessageSerializer,
    MarkOutboxDeadSerializer,
    OutboxHealthQuerySerializer,
    OutboxMessageSerializer,
    RequeueStuckOutboxSerializer,
    RetryOutboxSerializer,
)
from apps.events.health import get_outbox_health
from apps.events.services import DomainEventService


def _limit(request, default: int = 100) -> int:
    try:
        return max(1, min(int(request.query_params.get('limit') or default), 500))
    except (TypeError, ValueError):
        return default


def _audit_admin_action(request, *, action: str, target_type: str, target_id: str, context=None, reason: str = '', status_value: str = 'accepted'):
    AuditService.log_admin_action(
        request=request,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        reason=reason,
        status=status_value,
        context=context or {},
    )


class EventHandlerListView(APIView):
    permission_classes = [IsAdminUser]
    service = DomainEventService()

    def get(self, request):
        return Response(EventHandlerSerializer(self.service.list_dispatch_handlers(), many=True).data)


class DomainEventListView(APIView):
    permission_classes = [IsAdminUser]
    service = DomainEventService()

    def get(self, request):
        payload = self.service.list_events(
            event_type=request.query_params.get('event_type') or None,
            aggregate_type=request.query_params.get('aggregate_type') or None,
            aggregate_id=request.query_params.get('aggregate_id') or None,
            tenant_id=request.query_params.get('tenant_id') or None,
            idempotency_key=request.query_params.get('idempotency_key') or None,
            limit=_limit(request),
        )
        return Response(DomainEventSerializer(payload, many=True).data)


class DomainEventDetailView(APIView):
    permission_classes = [IsAdminUser]
    service = DomainEventService()

    def get(self, request, event_id: str):
        try:
            payload = self.service.get_event(event_id=event_id)
        except ObjectDoesNotExist:
            return Response({'detail': 'Domain event was not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(DomainEventSerializer(payload).data)


class OutboxHealthView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = OutboxHealthQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(get_outbox_health(**serializer.validated_data))


class OutboxMessageListView(APIView):
    permission_classes = [IsAdminUser]
    service = DomainEventService()

    def get(self, request):
        payload = self.service.list_outbox(
            status=request.query_params.get('status') or None,
            topic=request.query_params.get('topic') or None,
            event_type=request.query_params.get('event_type') or None,
            aggregate_type=request.query_params.get('aggregate_type') or None,
            aggregate_id=request.query_params.get('aggregate_id') or None,
            limit=_limit(request),
        )
        return Response(OutboxMessageSerializer(payload, many=True).data)


class OutboxMessageDetailView(APIView):
    permission_classes = [IsAdminUser]
    service = DomainEventService()

    def get(self, request, message_id: str):
        try:
            payload = self.service.get_outbox(message_id=message_id)
        except ObjectDoesNotExist:
            return Response({'detail': 'Outbox message was not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(OutboxMessageSerializer(payload).data)


class OutboxMessageRetryView(APIView):
    permission_classes = [IsAdminUser]
    service = DomainEventService()

    def post(self, request, message_id: str):
        serializer = RetryOutboxSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = self.service.retry_outbox_message(message_id=message_id, **serializer.validated_data)
        except ObjectDoesNotExist:
            return Response({'detail': 'Outbox message was not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_409_CONFLICT)
        _audit_admin_action(
            request,
            action='outbox.retry',
            target_type='outbox_message',
            target_id=message_id,
            context={'input': serializer.validated_data, 'result': {'status': payload.get('status'), 'attempts': payload.get('attempts')}},
        )
        return Response(OutboxMessageSerializer(payload).data, status=status.HTTP_202_ACCEPTED)


class OutboxMessageMarkDeadView(APIView):
    permission_classes = [IsAdminUser]
    service = DomainEventService()

    def post(self, request, message_id: str):
        serializer = MarkOutboxDeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = self.service.mark_outbox_dead(message_id=message_id, **serializer.validated_data)
        except ObjectDoesNotExist:
            return Response({'detail': 'Outbox message was not found.'}, status=status.HTTP_404_NOT_FOUND)
        _audit_admin_action(
            request,
            action='outbox.mark_dead',
            target_type='outbox_message',
            target_id=message_id,
            reason=serializer.validated_data.get('reason', ''),
            context={'result': {'status': payload.get('status'), 'last_error': payload.get('last_error', '')}},
        )
        return Response(OutboxMessageSerializer(payload).data, status=status.HTTP_202_ACCEPTED)


class InboxMessageListView(APIView):
    permission_classes = [IsAdminUser]
    service = DomainEventService()

    def get(self, request):
        payload = self.service.list_inbox(
            consumer=request.query_params.get('consumer') or None,
            status=request.query_params.get('status') or None,
            limit=_limit(request),
        )
        return Response(InboxMessageSerializer(payload, many=True).data)


class EmitEventView(APIView):
    permission_classes = [IsAdminUser]
    service = DomainEventService()

    def post(self, request):
        serializer = EmitEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.service.emit(**serializer.validated_data)
        _audit_admin_action(
            request,
            action='events.emit',
            target_type='domain_event',
            target_id=payload.get('event_id', ''),
            context={'input': serializer.validated_data, 'result': payload},
        )
        return Response(payload, status=status.HTTP_202_ACCEPTED)


class DispatchOutboxView(APIView):
    permission_classes = [IsAdminUser]
    service = DomainEventService()

    def post(self, request):
        serializer = DispatchOutboxSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.service.dispatch_pending_batch(**serializer.validated_data)
        _audit_admin_action(
            request,
            action='outbox.dispatch',
            target_type='outbox_batch',
            target_id='dispatch',
            context={'input': serializer.validated_data, 'result': payload},
        )
        return Response(payload, status=status.HTTP_202_ACCEPTED)


class RequeueStuckOutboxView(APIView):
    permission_classes = [IsAdminUser]
    service = DomainEventService()

    def post(self, request):
        serializer = RequeueStuckOutboxSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = self.service.requeue_stuck_processing(**serializer.validated_data)
        _audit_admin_action(
            request,
            action='outbox.requeue_stuck',
            target_type='outbox_batch',
            target_id='requeue_stuck',
            context={'input': serializer.validated_data, 'result': payload},
        )
        return Response(payload, status=status.HTTP_202_ACCEPTED)
