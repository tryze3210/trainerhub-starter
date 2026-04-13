from rest_framework import serializers
from apps.videos.models import MediaAsset, Video


class UploadIntentRequestSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=128)
    file_size_bytes = serializers.IntegerField(min_value=1)
    visibility = serializers.ChoiceField(choices=["private", "public"])

    def validate_content_type(self, value):
        allowed = {"video/mp4", "video/quicktime", "image/jpeg", "image/png", "image/webp"}
        if value not in allowed:
            raise serializers.ValidationError("Unsupported content type")
        return value


class CompleteUploadSerializer(serializers.Serializer):
    checksum_sha256 = serializers.CharField(required=False, allow_blank=True)


class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = (
            "id",
            "bucket_name",
            "object_key",
            "asset_type",
            "visibility",
            "status",
            "content_type",
            "file_size_bytes",
            "original_filename",
            "checksum_sha256",
            "metadata_json",
        )


class VideoSerializer(serializers.ModelSerializer):
    media_asset_id = serializers.UUIDField(write_only=True, required=False)
    media_asset = MediaAssetSerializer(read_only=True)

    class Meta:
        model = Video
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "duration_seconds",
            "is_free",
            "status",
            "media_asset_id",
            "media_asset",
        )
        read_only_fields = ("id", "status", "media_asset")
