from rest_framework import serializers
from apps.orders.models import Order, OrderItem
from apps.payments.models import PaymentProvider


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'item_type', 'item_id', 'title_snapshot', 'quantity', 'unit_price', 'total_price', 'metadata']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_type',
            'status',
            'currency',
            'total_amount',
            'external_checkout_id',
            'paid_at',
            'completed_at',
            'created_at',
            'updated_at',
            'items',
        ]


class CreateCheckoutSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=['one_time', 'subscription'])
    item_type = serializers.ChoiceField(choices=['video', 'program', 'bundle'], required=False)
    # Public content currently exposes integer ids, slugs and source_draft UUIDs in different places.
    # The service resolves all three and stores the canonical source_draft UUID in OrderItem.item_id.
    item_id = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    currency = serializers.CharField(required=False, allow_blank=True, default='RUB')
    plan_id = serializers.UUIDField(required=False)
    provider = serializers.ChoiceField(choices=PaymentProvider.choices, required=False, default=PaymentProvider.MOCK)
