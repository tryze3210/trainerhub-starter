from rest_framework import serializers
from apps.trainers.models import TrainerProfile


class TrainerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerProfile
        fields = (
            "id",
            "slug",
            "display_name",
            "headline",
            "bio",
            "rating_avg",
            "views_count",
            "sales_count",
            "status",
            "is_public",
        )
        read_only_fields = ("id", "rating_avg", "views_count", "sales_count", "status")
