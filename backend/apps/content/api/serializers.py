from rest_framework import serializers
from apps.content.models import PublishedBundle, PublishedBundleItem, PublishedLesson, PublishedProgram, PublishedVideo


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


class PublishedBundleItemSerializer(serializers.ModelSerializer):
    target_title = serializers.SerializerMethodField()

    class Meta:
        model = PublishedBundleItem
        fields = '__all__'

    def get_target_title(self, obj):
        if obj.item_type == PublishedBundleItem.ItemType.VIDEO:
            target = PublishedVideo.objects.filter(slug=obj.target_slug).only('title').first()
        else:
            target = PublishedProgram.objects.filter(slug=obj.target_slug).only('title').first()
        return getattr(target, 'title', obj.target_slug)


class PublishedBundleSerializer(serializers.ModelSerializer):
    trainer_slug = serializers.CharField(source='trainer_profile.slug', read_only=True)
    trainer_name = serializers.CharField(source='trainer_profile.display_name', read_only=True)
    items = PublishedBundleItemSerializer(many=True, read_only=True)

    class Meta:
        model = PublishedBundle
        fields = '__all__'
