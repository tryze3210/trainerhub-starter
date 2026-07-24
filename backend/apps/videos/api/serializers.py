from pathlib import PurePath
import re

from django.conf import settings
from rest_framework import serializers

from apps.videos.models import MediaAsset, Video


UPLOAD_CONTENT_TYPE_EXTENSIONS = {
    "video/mp4": {"mp4"},
    "video/quicktime": {"mov", "qt"},
    "image/jpeg": {"jpg", "jpeg"},
    "image/png": {"png"},
    "image/webp": {"webp"},
}
DEFAULT_MAX_UPLOAD_BYTES = 5 * 1024 * 1024 * 1024
CHECKSUM_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")


class UploadIntentRequestSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=128)
    file_size_bytes = serializers.IntegerField(min_value=1)
    visibility = serializers.ChoiceField(choices=["private", "public"])

    def validate_filename(self, value):
        filename = PurePath(str(value).replace("\\", "/")).name.strip()
        if not filename or filename in {".", ".."}:
            raise serializers.ValidationError("Invalid filename")
        if "\x00" in filename:
            raise serializers.ValidationError("Invalid filename")
        if "." not in filename or filename.rsplit(".", 1)[-1].strip() == "":
            raise serializers.ValidationError("Filename extension is required")
        return filename

    def validate_content_type(self, value):
        if value not in UPLOAD_CONTENT_TYPE_EXTENSIONS:
            raise serializers.ValidationError("Unsupported content type")
        return value

    def validate_file_size_bytes(self, value):
        max_size = int(getattr(settings, "MEDIA_MAX_UPLOAD_BYTES", DEFAULT_MAX_UPLOAD_BYTES))
        if value > max_size:
            raise serializers.ValidationError(f"File is larger than {max_size} bytes")
        return value

    def validate(self, attrs):
        extension = attrs["filename"].rsplit(".", 1)[-1].lower()
        allowed_extensions = UPLOAD_CONTENT_TYPE_EXTENSIONS[attrs["content_type"]]
        if extension not in allowed_extensions:
            raise serializers.ValidationError({"filename": "Filename extension does not match content type"})
        return attrs


class CompleteUploadSerializer(serializers.Serializer):
    checksum_sha256 = serializers.CharField(required=False, allow_blank=True)

    def validate_checksum_sha256(self, value):
        if value and not CHECKSUM_SHA256_RE.fullmatch(value):
            raise serializers.ValidationError("Checksum must be a sha256 hex digest")
        return value.lower() if value else value


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
