from rest_framework import serializers


class PublicCatalogItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    entity_type = serializers.CharField()
    slug = serializers.CharField()
    title = serializers.CharField()
    trainer_slug = serializers.CharField()
    trainer_name = serializers.CharField()
    category = serializers.CharField()
    difficulty = serializers.CharField()
    price = serializers.CharField()
    currency = serializers.CharField()
    rating = serializers.FloatField()
    reviews_count = serializers.IntegerField()
    duration_minutes = serializers.IntegerField()
    is_featured = serializers.BooleanField()
    cover_url = serializers.URLField()
    description = serializers.CharField()
    published_at = serializers.CharField()


class CatalogResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    items = PublicCatalogItemSerializer(many=True)
    applied_filters = serializers.DictField()
