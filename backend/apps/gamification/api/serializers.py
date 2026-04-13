from rest_framework import serializers

from apps.gamification.models import BadgeDefinition, LeaderboardSnapshot, RewardRule


class RewardRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardRule
        fields = '__all__'


class BadgeDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BadgeDefinition
        fields = '__all__'


class LeaderboardSnapshotSerializer(serializers.ModelSerializer):
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = LeaderboardSnapshot
        fields = ['id', 'period', 'snapshot_date', 'rank', 'user', 'user_display', 'points', 'streak_days', 'badge_count', 'cohort_id']

    def get_user_display(self, obj):
        return getattr(obj.user, 'get_full_name', lambda: '')() or getattr(obj.user, 'email', '') or str(obj.user_id)
