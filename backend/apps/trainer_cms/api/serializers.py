from rest_framework import serializers
from apps.trainer_cms.models import ProgramLessonDraft, TrainerBundleDraft, TrainerProgramDraft, TrainerVideoDraft


class TrainerVideoDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerVideoDraft
        fields = "__all__"
        read_only_fields = ("trainer_id", "current_version_number", "created_at", "updated_at")


class TrainerProgramDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerProgramDraft
        fields = "__all__"
        read_only_fields = ("trainer_id", "current_version_number", "created_at", "updated_at")


class ProgramLessonDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramLessonDraft
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class TrainerBundleDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerBundleDraft
        fields = "__all__"
        read_only_fields = ("trainer_id", "created_at", "updated_at")
