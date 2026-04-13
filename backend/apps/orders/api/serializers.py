from rest_framework import serializers
from apps.orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'item_type', 'item_id', 'title_snapshot', 'quantity', 'unit_price', 'total_price', 'metadata']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_type', 'status', 'currency', 'total_amount', 'paid_at', 'completed_at', 'items']


class CreateCheckoutSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=['one_time', 'subscription'])
    item_type = serializers.CharField(required=False)
    item_id = serializers.UUIDField(required=False)
    title = serializers.CharField(required=False)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    plan_id = serializers.UUIDField(required=False)
