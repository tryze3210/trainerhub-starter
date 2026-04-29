from rest_framework import serializers
from apps.trainers.models import TrainerApplication, TrainerProfile


class TrainerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerProfile
        fields = (
            'id',
            'slug',
            'display_name',
            'headline',
            'bio',
            'rating_avg',
            'views_count',
            'sales_count',
            'status',
            'is_public',
        )
        read_only_fields = ('id', 'rating_avg', 'views_count', 'sales_count', 'status')


class TrainerApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerApplication
        fields = (
            'status',
            'legal_name',
            'brand_name',
            'contact_phone',
            'country',
            'city',
            'specialties',
            'links',
            'bio',
            'experience_years',
            'submitted_at',
            'reviewed_at',
            'reviewer_note',
            'latest_moderation_case_id',
            'moderation_snapshot',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('status', 'submitted_at', 'reviewed_at', 'reviewer_note', 'latest_moderation_case_id', 'moderation_snapshot', 'created_at', 'updated_at')


class TrainerApplicationUpsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerApplication
        fields = (
            'legal_name',
            'brand_name',
            'contact_phone',
            'country',
            'city',
            'specialties',
            'links',
            'bio',
            'experience_years',
        )
