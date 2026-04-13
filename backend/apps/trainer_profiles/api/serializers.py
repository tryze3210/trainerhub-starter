from rest_framework import serializers

from apps.public_catalog.api.serializers import PublicCatalogItemSerializer


class PublicTrainerSerializer(serializers.Serializer):
    id = serializers.CharField()
    slug = serializers.CharField()
    display_name = serializers.CharField()
    headline = serializers.CharField()
    bio = serializers.CharField()
    avatar_url = serializers.URLField()
    specialties = serializers.ListField(child=serializers.CharField())
    languages = serializers.ListField(child=serializers.CharField())
    rating = serializers.FloatField()
    reviews_count = serializers.IntegerField()
    students_count = serializers.IntegerField()
    active_products_count = serializers.IntegerField()
    featured_items = serializers.ListField(child=serializers.CharField())


class PublicTrainerDetailSerializer(PublicTrainerSerializer):
    catalog_items = PublicCatalogItemSerializer(many=True)
