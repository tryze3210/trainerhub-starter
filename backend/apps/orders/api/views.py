from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.orders.api.serializers import CreateCheckoutSerializer, OrderSerializer
from apps.orders.checkout_integrity import CheckoutIntegrityService
from apps.orders.models import Order
from apps.subscriptions.models import SubscriptionPlan


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items').order_by('-created_at')

    def _request_idempotency_key(self, serializer_data):
        body_value = serializer_data.get('idempotency_key') or ''
        header_value = self.request.headers.get('Idempotency-Key') or self.request.headers.get('X-Idempotency-Key') or ''
        return body_value or header_value

    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        serializer = CreateCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        idempotency_key = self._request_idempotency_key(data)
        try:
            if data['mode'] == 'subscription':
                plan = SubscriptionPlan.objects.get(id=data['plan_id'], is_active=True)
                result = CheckoutIntegrityService.create_subscription_checkout(
                    user=request.user,
                    plan=plan,
                    provider=data.get('provider'),
                    idempotency_key=idempotency_key,
                )
            else:
                result = CheckoutIntegrityService.create_one_time_checkout(
                    user=request.user,
                    item_type=data['item_type'],
                    item_id=data['item_id'],
                    title=data.get('title'),
                    amount=data.get('amount'),
                    currency=data.get('currency') or 'RUB',
                    provider=data.get('provider'),
                    idempotency_key=idempotency_key,
                )
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'detail': 'Subscription plan was not found or inactive.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except (KeyError, ValueError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        response_status = status.HTTP_200_OK if result.reused_order else status.HTTP_201_CREATED
        return Response(
            {
                'order': OrderSerializer(result.order).data,
                'payment': {
                    'id': str(result.payment.id),
                    'provider': result.payment.provider,
                    'status': result.payment.status,
                    'checkout_url': result.payment.external_checkout_url,
                    'external_checkout_url': result.payment.external_checkout_url,
                    'external_payment_id': result.payment.external_payment_id,
                    'provider_payload': result.payment.provider_payload,
                },
                'checkout_integrity': {
                    **result.integrity,
                    'reused_order': result.reused_order,
                    'reused_payment': result.reused_payment,
                },
            },
            status=response_status,
        )
