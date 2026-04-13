from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from apps.payments.api.serializers import PaymentSerializer, PaymentWebhookSerializer
from apps.payments.models import Payment
from apps.payments.services import PaymentWebhookService


class PaymentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user).order_by('-created_at')


class PaymentWebhookViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = PaymentWebhookSerializer

    @action(detail=False, methods=['post'], url_path='receive')
    def receive(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = PaymentWebhookService.handle(**serializer.validated_data)
        return Response({'webhook_event_id': str(event.id), 'processed_at': event.processed_at}, status=status.HTTP_200_OK)
