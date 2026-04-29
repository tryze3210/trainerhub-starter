from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from apps.payments.api.serializers import PaymentSerializer, PaymentWebhookSerializer
from apps.payments.models import Payment, PaymentStatus
from apps.payments.services import PaymentService, PaymentWebhookService


class PaymentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='confirm-mock')
    def confirm_mock(self, request, pk=None):
        payment = self.get_object()
        updated = PaymentService.mark_succeeded(payment=payment, provider_payload={**(payment.provider_payload or {}), 'confirmed_via': 'mock_ui'})
        return Response(self.get_serializer(updated).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancel-mock')
    def cancel_mock(self, request, pk=None):
        payment = self.get_object()
        updated = PaymentService.mark_cancelled(payment=payment, provider_payload={**(payment.provider_payload or {}), 'cancelled_via': 'mock_ui'})
        return Response(self.get_serializer(updated).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='provider-return')
    def provider_return(self, request):
        payment_id = request.query_params.get('payment_id')
        status_value = (request.query_params.get('status') or '').strip().lower()
        if not payment_id:
            return Response({'detail': 'payment_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        payment = Payment.objects.get(pk=payment_id)
        if status_value in {'success', 'succeeded', 'paid'}:
            payment = PaymentService.mark_succeeded(payment=payment, provider_payload={**(payment.provider_payload or {}), 'return_status': status_value})
            redirect_path = f'/checkout/success?order_id={payment.order_id}&payment_id={payment.id}'
        elif status_value in {'cancel', 'cancelled'}:
            payment = PaymentService.mark_cancelled(payment=payment, provider_payload={**(payment.provider_payload or {}), 'return_status': status_value})
            redirect_path = f'/checkout/cancel?order_id={payment.order_id}&payment_id={payment.id}'
        elif status_value in {'failed', 'error'}:
            payment = PaymentService.mark_failed(payment=payment, provider_payload={**(payment.provider_payload or {}), 'return_status': status_value})
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


class PaymentWebhookViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = PaymentWebhookSerializer

    @action(detail=False, methods=['post'], url_path='receive')
    def receive(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = PaymentWebhookService.handle(**serializer.validated_data)
        return Response({'webhook_event_id': str(event.id), 'processed_at': event.processed_at}, status=status.HTTP_200_OK)
