from rest_framework import serializers
from apps.content.models import PublishedBundle, PublishedLesson, PublishedProgram, PublishedVideo


class PublishedVideoSerializer(serializers.ModelSerializer):
    trainer_slug = serializers.CharField(source='trainer_profile.slug', read_only=True)
    trainer_name = serializers.CharField(source='trainer_profile.display_name', read_only=True)

    class Meta:
        model = PublishedVideo
        fields = '__all__'


class PublishedLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublishedLesson
        fields = '__all__'


class PublishedProgramSerializer(serializers.ModelSerializer):
    trainer_slug = serializers.CharField(source='trainer_profile.slug', read_only=True)
    trainer_name = serializers.CharField(source='trainer_profile.display_name', read_only=True)
    lessons = PublishedLessonSerializer(many=True, read_only=True)

    class Meta:
        model = PublishedProgram
        fields = '__all__'


class PublishedBundleSerializer(serializers.ModelSerializer):
    trainer_slug = serializers.CharField(source='trainer_profile.slug', read_only=True)
    trainer_name = serializers.CharField(source='trainer_profile.display_name', read_only=True)

    class Meta:
        model = PublishedBundle
        fields = '__all__'
