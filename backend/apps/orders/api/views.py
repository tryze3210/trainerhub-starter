from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.orders.api.serializers import CreateCheckoutSerializer, OrderSerializer
from apps.orders.models import Order
from apps.orders.services import OrderService
from apps.payments.services import PaymentService
from apps.subscriptions.models import SubscriptionPlan


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items').order_by('-created_at')

    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        serializer = CreateCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            if data['mode'] == 'subscription':
                plan = SubscriptionPlan.objects.get(id=data['plan_id'], is_active=True)
                order = OrderService.create_subscription_order(user=request.user, plan=plan)
            else:
                order = OrderService.create_one_time_order(
                    user=request.user,
                    item_type=data['item_type'],
                    item_id=data['item_id'],
                    title=data.get('title'),
                    amount=data.get('amount'),
                    currency=data.get('currency') or 'RUB',
                )
            payment = PaymentService.create_checkout_payment(order=order, provider=data.get('provider'))
        except SubscriptionPlan.DoesNotExist:
            return Response({'detail': 'Subscription plan was not found or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        except (KeyError, ValueError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'order': OrderSerializer(order).data,
            'payment': {
                'id': str(payment.id),
                'provider': payment.provider,
                'status': payment.status,
                'checkout_url': payment.external_checkout_url,
                'external_checkout_url': payment.external_checkout_url,
                'external_payment_id': payment.external_payment_id,
                'provider_payload': payment.provider_payload,
            },
        }, status=status.HTTP_201_CREATED)
