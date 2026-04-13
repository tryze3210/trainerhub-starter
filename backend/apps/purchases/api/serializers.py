from rest_framework import serializers
from apps.purchases.models import Purchase


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = (
            "id",
            "customer",
            "trainer",
            "product",
            "status",
            "gross_amount",
            "platform_commission_amount",
            "trainer_net_amount",
            "currency",
            "created_at",
        )
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
