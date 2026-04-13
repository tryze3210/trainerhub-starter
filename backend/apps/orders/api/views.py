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

        if data['mode'] == 'subscription':
            plan = SubscriptionPlan.objects.get(id=data['plan_id'])
            order = OrderService.create_subscription_order(user=request.user, plan=plan)
        else:
            order = OrderService.create_one_time_order(
                user=request.user,
                item_type=data['item_type'],
                item_id=data['item_id'],
                title=data['title'],
                amount=data['amount'],
            )
        payment = PaymentService.create_checkout_payment(order=order)
        return Response({
            'order': OrderSerializer(order).data,
            'payment': {
                'id': str(payment.id),
                'status': payment.status,
                'checkout_url': payment.external_checkout_url,
            },
        }, status=status.HTTP_201_CREATED)
