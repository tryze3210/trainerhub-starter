from rest_framework import serializers

from apps.progress.models import LessonProgress, ProgramProgress, VideoProgress


class SaveVideoProgressSerializer(serializers.Serializer):
    video_id = serializers.CharField()
    watched_seconds = serializers.IntegerField(min_value=0)
    last_position_seconds = serializers.IntegerField(min_value=0)


class MarkLessonCompletedSerializer(serializers.Serializer):
    lesson_id = serializers.CharField()
    program_id = serializers.CharField(required=False, allow_blank=True)
    content_type = serializers.ChoiceField(choices=['program', 'course'], required=False)


class VideoProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoProgress
        fields = ['id', 'video_id', 'watched_seconds', 'duration_seconds', 'completion_percent', 'is_completed', 'last_position_seconds', 'last_watched_at', 'updated_at']


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ['id', 'lesson_id', 'program_id', 'content_type', 'is_completed', 'completed_at', 'updated_at']


class ProgramProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramProgress
        fields = ['id', 'program_id', 'content_type', 'total_lessons', 'completed_lessons', 'completion_percent', 'is_completed', 'completed_at', 'last_activity_at', 'updated_at']
