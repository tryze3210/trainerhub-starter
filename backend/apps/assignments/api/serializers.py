import ipaddress
from urllib.parse import urlparse

from rest_framework import serializers

from apps.assignments.models import AssignmentContentType, AssignmentStatus, SubmissionStatus

MAX_SUBMISSION_ATTACHMENTS = 10
MAX_ATTACHMENT_SIZE_BYTES = 100 * 1024 * 1024
ALLOWED_ATTACHMENT_FIELDS = {"url", "title", "content_type", "size_bytes"}
LOCAL_ATTACHMENT_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def _is_private_host(hostname: str) -> bool:
    if not hostname:
        return True
    normalized = hostname.strip().lower()
    if normalized in LOCAL_ATTACHMENT_HOSTS:
        return True
    try:
        ip_address = ipaddress.ip_address(normalized)
    except ValueError:
        return False
    return bool(ip_address.is_private or ip_address.is_loopback or ip_address.is_link_local)


class AssignmentCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    content_type = serializers.ChoiceField(choices=AssignmentContentType.choices)
    content_id = serializers.CharField(max_length=80)
    lesson_id = serializers.CharField(max_length=80, required=False, allow_blank=True)
    due_at = serializers.DateTimeField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=AssignmentStatus.choices, required=False)
    metadata = serializers.JSONField(required=False)


class AssignmentSubmitSerializer(serializers.Serializer):
    answer_text = serializers.CharField(required=False, allow_blank=True)
    attachments = serializers.ListField(child=serializers.DictField(), required=False)

    def validate_attachments(self, value):
        if len(value or []) > MAX_SUBMISSION_ATTACHMENTS:
            raise serializers.ValidationError(f"No more than {MAX_SUBMISSION_ATTACHMENTS} attachments are allowed")
        normalized = []
        for index, item in enumerate(value or []):
            unknown_fields = set(item.keys()) - ALLOWED_ATTACHMENT_FIELDS
            if unknown_fields:
                raise serializers.ValidationError({index: f"Unsupported attachment fields: {', '.join(sorted(unknown_fields))}"})
            raw_url = str(item.get("url") or "").strip()
            parsed = urlparse(raw_url)
            if parsed.scheme != "https" or not parsed.netloc:
                raise serializers.ValidationError({index: "Attachment url must be an absolute https URL"})
            if _is_private_host(parsed.hostname or ""):
                raise serializers.ValidationError({index: "Attachment url must not point to a local or private host"})
            size_bytes = item.get("size_bytes")
            if size_bytes not in (None, ""):
                try:
                    size_bytes = int(size_bytes)
                except (TypeError, ValueError):
                    raise serializers.ValidationError({index: "Attachment size_bytes must be an integer"})
                if size_bytes < 0 or size_bytes > MAX_ATTACHMENT_SIZE_BYTES:
                    raise serializers.ValidationError({index: f"Attachment size_bytes must be between 0 and {MAX_ATTACHMENT_SIZE_BYTES}"})
            normalized_item = {
                "url": raw_url,
                "title": str(item.get("title") or "").strip()[:160],
                "content_type": str(item.get("content_type") or "").strip()[:128],
            }
            if size_bytes not in (None, ""):
                normalized_item["size_bytes"] = size_bytes
            normalized.append(normalized_item)
        return normalized


class AssignmentReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            (SubmissionStatus.REVIEWED, "Reviewed"),
            (SubmissionStatus.NEEDS_REVISION, "Needs revision"),
            (SubmissionStatus.APPROVED, "Approved"),
        ],
        required=False,
    )
    review_comment = serializers.CharField(required=False, allow_blank=True)
    score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
