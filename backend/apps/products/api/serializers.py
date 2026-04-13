from rest_framework import serializers
from apps.products.models import Product, ProductItem


class ProductItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductItem
        fields = ("id", "video", "position")


class ProductSerializer(serializers.ModelSerializer):
    item_video_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )
    items = ProductItemSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "product_type",
            "access_type",
            "status",
            "currency",
            "price_amount",
            "item_video_ids",
            "items",
        )
        read_only_fields = ("id",)
