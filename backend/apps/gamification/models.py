import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class RewardRule(models.Model):
    EVENT_CHOICES = [
        ('daily_checkin_completed', 'Daily check-in completed'),
        ('habit_streak_milestone', 'Habit streak milestone'),
        ('cohort_checkpoint_completed', 'Cohort checkpoint completed'),
        ('live_session_attended', 'Live session attended'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True)
    event_type = models.CharField(max_length=64, choices=EVENT_CHOICES)
    points_delta = models.IntegerField(default=0)
    badge_code = models.CharField(max_length=64, blank=True)
    min_streak_days = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']


class BadgeDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=128, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']


class UserBadge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gamification_badges')
    badge = models.ForeignKey(BadgeDefinition, on_delete=models.CASCADE, related_name='awards')
    awarded_at = models.DateTimeField(default=timezone.now)
    source_event_type = models.CharField(max_length=64, blank=True)
    source_event_id = models.CharField(max_length=64, blank=True)

    class Meta:
        unique_together = [('user', 'badge')]
        ordering = ['-awarded_at']


class AchievementLedger(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achievement_ledger_entries')
    event_type = models.CharField(max_length=64)
    source_event_id = models.CharField(max_length=64, blank=True)
    reward_rule = models.ForeignKey(RewardRule, on_delete=models.SET_NULL, null=True, blank=True)
    points_delta = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'created_at']), models.Index(fields=['event_type'])]


class UserRewardBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reward_balance')
    total_points = models.IntegerField(default=0)
    lifetime_points = models.IntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-total_points']


class LeaderboardSnapshot(models.Model):
    PERIOD_CHOICES = [('weekly', 'Weekly'), ('monthly', 'Monthly'), ('all_time', 'All time')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.CharField(max_length=16, choices=PERIOD_CHOICES)
    snapshot_date = models.DateField()
    rank = models.PositiveIntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leaderboard_rows')
    points = models.IntegerField(default=0)
    streak_days = models.PositiveIntegerField(default=0)
    badge_count = models.PositiveIntegerField(default=0)
    cohort_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('period', 'snapshot_date', 'rank'), ('period', 'snapshot_date', 'user', 'cohort_id')]
        ordering = ['period', '-snapshot_date', 'rank']
        indexes = [models.Index(fields=['period', 'snapshot_date', 'rank'])]
