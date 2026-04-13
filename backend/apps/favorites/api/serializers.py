from rest_framework import serializers
from apps.favorites.models import Favorite

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'target_type', 'target_id', 'created_at']
