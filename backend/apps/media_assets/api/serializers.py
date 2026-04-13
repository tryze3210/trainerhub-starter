from rest_framework import serializers
from apps.media_assets.models import MediaAsset


class CreateUploadSessionSerializer(serializers.Serializer):
    asset_type = serializers.ChoiceField(choices=MediaAsset.Type.choices)
    filename = serializers.CharField(max_length=255)
    title = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=128)


class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = [
            "id", "asset_type", "title", "storage_key", "upload_status", "moderation_status",
            "mime_type", "size_bytes", "duration_seconds", "width", "height", "created_at", "updated_at",
        ]
