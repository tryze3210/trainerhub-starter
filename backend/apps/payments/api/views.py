import json

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.access_control.permissions import IsAdminSupportFinanceReadonly, IsAdminOrSupport
from apps.audit.services import AuditService
from apps.payments.api.serializers import AdminPaymentSerializer, PaymentRefundSerializer, PaymentSerializer, PaymentWebhookEventSerializer, PaymentWebhookSerializer
from apps.payments.gateway import mock_payments_allowed
from apps.payments.models import Payment, PaymentStatus, PaymentWebhookEvent
from apps.payments.services import PaymentService, PaymentWebhookService
from apps.payments.webhook_security import PaymentWebhookPayloadError, PaymentWebhookSecurity, PaymentWebhookSignatureError
from apps.tenancy.scoping import scope_payment_webhooks_for_user, scope_payments_for_user


class PaymentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user).order_by('-created_at')

    def _assert_mock_payments_allowed(self):
        if not mock_payments_allowed():
            raise PermissionDenied('Mock payment actions are disabled for this environment.')

    @action(detail=True, methods=['post'], url_path='confirm-mock')
    def confirm_mock(self, request, pk=None):
        self._assert_mock_payments_allowed()
        payment = self.get_object()
        updated = PaymentService.mark_succeeded(payment=payment, provider_payload={**(payment.provider_payload or {}), 'confirmed_via': 'mock_ui'})
        return Response(self.get_serializer(updated).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancel-mock')
    def cancel_mock(self, request, pk=None):
        self._assert_mock_payments_allowed()
        payment = self.get_object()
        updated = PaymentService.mark_cancelled(payment=payment, provider_payload={**(payment.provider_payload or {}), 'cancelled_via': 'mock_ui'})
        return Response(self.get_serializer(updated).data, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'], url_path='refund-mock')
    def refund_mock(self, request, pk=None):
        self._assert_mock_payments_allowed()
        payment = self.get_object()
        serializer = PaymentRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = PaymentService.mark_refunded(
            payment=payment,
            provider_payload={**(payment.provider_payload or {}), 'refunded_via': 'mock_ui'},
            amount=serializer.validated_data.get('amount'),
            refund_id=serializer.validated_data.get('refund_id', ''),
            reason=serializer.validated_data.get('reason', ''),
            request=request,
        )
        return Response(self.get_serializer(updated).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='dispute-mock')
    def dispute_mock(self, request, pk=None):
        self._assert_mock_payments_allowed()
        payment = self.get_object()
        updated = PaymentService.mark_disputed(
            payment=payment,
            provider_payload={**(payment.provider_payload or {}), 'disputed_via': 'mock_ui'},
        )
        return Response(self.get_serializer(updated).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='chargeback-lost-mock')
    def chargeback_lost_mock(self, request, pk=None):
        self._assert_mock_payments_allowed()
        payment = self.get_object()
        updated = PaymentService.mark_chargeback_lost(
            payment=payment,
            provider_payload={**(payment.provider_payload or {}), 'chargeback_lost_via': 'mock_ui'},
        )
        return Response(self.get_serializer(updated).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='chargeback-won-mock')
    def chargeback_won_mock(self, request, pk=None):
        self._assert_mock_payments_allowed()
        payment = self.get_object()
        updated = PaymentService.mark_chargeback_won(
            payment=payment,
            provider_payload={**(payment.provider_payload or {}), 'chargeback_won_via': 'mock_ui'},
        )
        return Response(self.get_serializer(updated).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='provider-return')
    def provider_return(self, request):
        payment_id = request.query_params.get('payment_id')
        if not payment_id:
            return Response({'detail': 'payment_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        payment = Payment.objects.get(pk=payment_id)

        if payment.status == PaymentStatus.SUCCEEDED:
            redirect_path = f'/checkout/success?order_id={payment.order_id}&payment_id={payment.id}'
        elif payment.status in {PaymentStatus.CANCELLED, PaymentStatus.FAILED}:
            redirect_path = f'/checkout/cancel?order_id={payment.order_id}&payment_id={payment.id}'
        else:
            redirect_path = f'/payments/{payment.id}'
        return Response({
            'payment_id': str(payment.id),
            'order_id': str(payment.order_id),
            'payment_status': payment.status,
            'order_status': payment.order.status,
            'redirect_path': redirect_path,
        }, status=status.HTTP_200_OK)


class AdminPaymentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = AdminPaymentSerializer
    permission_classes = [IsAdminSupportFinanceReadonly]

    def get_queryset(self):
        queryset = (
            scope_payments_for_user(Payment.objects.all(), self.request.user)
            .select_related('order', 'order__user')
            .prefetch_related('order__granted_entitlements')
            .order_by('-created_at')
        )

        status_value = self.request.query_params.get('status')
        provider = self.request.query_params.get('provider')
        order_id = self.request.query_params.get('order_id')
        external_payment_id = self.request.query_params.get('external_payment_id')
        buyer_email = self.request.query_params.get('buyer_email')

        if status_value:
            queryset = queryset.filter(status=status_value)
        if provider:
            queryset = queryset.filter(provider=provider)
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        if external_payment_id:
            queryset = queryset.filter(external_payment_id=external_payment_id)
        if buyer_email:
            queryset = queryset.filter(order__user__email__icontains=buyer_email)

        if self.action == 'list':
            try:
                limit = int(self.request.query_params.get('limit') or 100)
            except (TypeError, ValueError):
                limit = 100
            return queryset[: max(1, min(limit, 500))]
        return queryset


class PaymentWebhookViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = PaymentWebhookEvent.objects.select_related('payment').order_by('-received_at', '-created_at')

    def get_serializer_class(self):
        if self.action == 'receive':
            return PaymentWebhookSerializer
        return PaymentWebhookEventSerializer

    def get_permissions(self):
        if self.action in {'receive'}:
            return [AllowAny()]
        if self.action in {'reprocess'}:
            return [IsAdminOrSupport()]
        return [IsAdminSupportFinanceReadonly()]

    def get_queryset(self):
        queryset = scope_payment_webhooks_for_user(super().get_queryset(), self.request.user)
        provider = self.request.query_params.get('provider')
        status_value = self.request.query_params.get('status')
        event_type = self.request.query_params.get('event_type')
        external_payment_id = self.request.query_params.get('external_payment_id')
        if provider:
            queryset = queryset.filter(provider=provider)
        if status_value:
            queryset = queryset.filter(status=status_value)
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if external_payment_id:
            queryset = queryset.filter(payload__external_payment_id=external_payment_id)
        return queryset

    def _audit_rejected_webhook(self, request, *, reason: str, raw_body: bytes | None = None, provider: str | None = None) -> None:
        body = raw_body if raw_body is not None else request.body
        if not body:
            body = json.dumps(request.data).encode('utf-8')
        provider_value = provider or request.query_params.get('provider') or request.headers.get('X-Payment-Provider') or ''
        AuditService.log(
            event_type='payment.webhook_rejected',
            entity_type='payment_webhook',
            entity_id=PaymentWebhookSecurity.raw_hash(body)[:32],
            context={
                'provider': provider_value,
                'reason': reason,
                'raw_payload_hash': PaymentWebhookSecurity.raw_hash(body),
                'headers': {
                    key: value
                    for key, value in dict(request.headers).items()
                    if key.lower().startswith('x-') or key.lower() in {'content-type', 'user-agent'}
                },
            },
            request=request,
        )

    @action(detail=False, methods=['post'], url_path='receive')
    def receive(self, request):
        raw_body = b''
        provider = None
        try:
            raw_body = request.body
            PaymentWebhookSecurity.validate_body_size(raw_body)
            provider = request.query_params.get('provider') or request.headers.get('X-Payment-Provider')
            event = PaymentWebhookService.handle_raw(
                provider=provider,
                payload=request.data,
                raw_body=raw_body,
                headers=dict(request.headers),
                verify_signature=True,
            )
        except PaymentWebhookSignatureError as exc:
            self._audit_rejected_webhook(request, reason=str(exc), raw_body=raw_body, provider=provider)
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except PaymentWebhookPayloadError as exc:
            self._audit_rejected_webhook(request, reason=str(exc), raw_body=raw_body, provider=provider)
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        data = PaymentWebhookEventSerializer(event).data
        return Response({
            'webhook_event_id': str(event.id),
            'status': event.status,
            'processed_at': event.processed_at,
            'event': data,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reprocess')
    def reprocess(self, request, pk=None):
        event = self.get_object()
        raw_force = request.data.get('force', False)
        force = raw_force if isinstance(raw_force, bool) else str(raw_force).strip().lower() in {'1', 'true', 'yes', 'on'}

        if event.status == PaymentWebhookEvent.Status.PROCESSED and not force:
            return Response(
                {
                    'detail': 'Webhook event is already processed. Pass force=true to reprocess it.',
                    'webhook_event_id': str(event.id),
                    'status': event.status,
                },
                status=status.HTTP_409_CONFLICT,
            )

        if force:
            event.status = PaymentWebhookEvent.Status.RECEIVED
            event.processed_at = None
            event.error_message = ''
            event.save(update_fields=['status', 'processed_at', 'error_message', 'updated_at'])

        try:
            updated = PaymentWebhookService.handle(
                provider=event.provider,
                event_type=event.event_type,
                external_event_id=event.external_event_id,
                payload=event.payload or {},
                headers=event.headers or {},
                signature=event.signature or '',
                raw_payload_hash=event.raw_payload_hash or '',
                verify_signature=False,
            )
        except Exception as exc:
            return Response(
                {
                    'detail': str(exc),
                    'webhook_event_id': str(event.id),
                    'status': PaymentWebhookEvent.Status.FAILED,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                'webhook_event_id': str(updated.id),
                'status': updated.status,
                'processed_at': updated.processed_at,
                'event': PaymentWebhookEventSerializer(updated).data,
            },
            status=status.HTTP_200_OK,
        )
