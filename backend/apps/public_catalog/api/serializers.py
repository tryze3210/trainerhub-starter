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


class PublicSeoSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    canonical_path = serializers.CharField()


class PublicCtaSerializer(serializers.Serializer):
    label = serializers.CharField()
    href = serializers.CharField()
    requires_auth = serializers.BooleanField(required=False)


class PublicPricingSerializer(serializers.Serializer):
    amount = serializers.CharField()
    currency = serializers.CharField()
    label = serializers.CharField()
    checkout_cta = PublicCtaSerializer()


class PublicReviewsSummarySerializer(serializers.Serializer):
    average_rating = serializers.FloatField()
    reviews_count = serializers.IntegerField()
    href = serializers.CharField()


class PublicMarketplaceHomeSerializer(serializers.Serializer):
    seo = PublicSeoSerializer()
    hero = serializers.DictField()
    catalog = CatalogResponseSerializer()
    featured = PublicCatalogItemSerializer(many=True)
    trust = serializers.DictField()


class PublicContentLandingSerializer(serializers.Serializer):
    seo = PublicSeoSerializer()
    item = PublicCatalogItemSerializer()
    pricing = PublicPricingSerializer()
    reviews = PublicReviewsSummarySerializer()
    trainer = serializers.DictField()
    access = serializers.DictField()


class PublicTrainerLandingSerializer(serializers.Serializer):
    seo = PublicSeoSerializer()
    profile = serializers.DictField()
    featured = PublicCatalogItemSerializer(many=True)
    catalog = serializers.DictField()
    reviews = PublicReviewsSummarySerializer()
    pricing = PublicPricingSerializer(many=True)
    checkout_ctas = PublicCtaSerializer(many=True)
