from __future__ import annotations

from rest_framework import serializers

from apps.products.models import Product, ProductItem
from apps.products.services import ACCESS_TYPES, PRODUCT_STATUSES, PRODUCT_TYPES, SUPPORTED_CURRENCIES


class TrainerProductItemSerializer(serializers.ModelSerializer):
    video_id = serializers.UUIDField(source="video.id", read_only=True)
    video_title = serializers.CharField(source="video.title", read_only=True)
    video_status = serializers.CharField(source="video.status", read_only=True)

    class Meta:
        model = ProductItem
        fields = ("id", "video", "video_id", "video_title", "video_status", "position")
        read_only_fields = fields


class TrainerProductSerializer(serializers.ModelSerializer):
    item_video_ids = serializers.ListField(child=serializers.UUIDField(), required=False, write_only=True)
    items = TrainerProductItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    readiness = serializers.SerializerMethodField()

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
            "items_count",
            "readiness",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "items", "items_count", "readiness", "created_at", "updated_at")
        extra_kwargs = {
            "slug": {"required": False, "allow_blank": True},
            "description": {"required": False, "allow_blank": True},
            "product_type": {"required": False},
            "access_type": {"required": False},
            "status": {"required": False},
            "currency": {"required": False},
            "price_amount": {"required": False},
        }

    def get_items_count(self, obj):
        return obj.items.count() if hasattr(obj, "items") else 0

    def get_readiness(self, obj):
        readiness = getattr(obj, "_readiness", None)
        return readiness

    def validate_product_type(self, value):
        if value and value not in PRODUCT_TYPES:
            raise serializers.ValidationError(f"Supported values: {', '.join(PRODUCT_TYPES)}.")
        return value

    def validate_access_type(self, value):
        if value and value not in ACCESS_TYPES:
            raise serializers.ValidationError(f"Supported values: {', '.join(ACCESS_TYPES)}.")
        return value

    def validate_status(self, value):
        if value and value not in PRODUCT_STATUSES:
            raise serializers.ValidationError(f"Supported values: {', '.join(PRODUCT_STATUSES)}.")
        return value

    def validate_currency(self, value):
        normalized = str(value or "RUB").upper()
        if normalized not in SUPPORTED_CURRENCIES:
            raise serializers.ValidationError(f"Supported values: {', '.join(SUPPORTED_CURRENCIES)}.")
        return normalized


class TrainerProductReadinessSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    status = serializers.CharField()
    blockers_count = serializers.IntegerField()
    checks = serializers.ListField(child=serializers.DictField())
