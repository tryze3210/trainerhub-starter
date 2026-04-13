from dataclasses import dataclass
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.gamification.models import (
    AchievementLedger,
    BadgeDefinition,
    RewardRule,
    UserBadge,
    UserRewardBalance,
)

User = get_user_model()


@dataclass
class AwardResult:
    points_delta: int
    badge_awarded: str | None
    ledger_id: str | None


class AchievementAwardingService:
    """
    Single integration seam for domain events from habits/cohorts/live_sessions.
    Do not call from views directly; invoke from application services.
    """

    @transaction.atomic
    def award_for_event(self, *, user: User, event_type: str, source_event_id: str = '', metadata: dict[str, Any] | None = None) -> AwardResult:
        metadata = metadata or {}
        rule = RewardRule.objects.filter(event_type=event_type, is_active=True).order_by('code').first()
        if not rule:
            return AwardResult(points_delta=0, badge_awarded=None, ledger_id=None)

        balance, _ = UserRewardBalance.objects.get_or_create(user=user)
        ledger = AchievementLedger.objects.create(
            user=user,
            event_type=event_type,
            source_event_id=source_event_id,
            reward_rule=rule,
            points_delta=rule.points_delta,
            metadata=metadata,
        )
        balance.total_points += rule.points_delta
        balance.lifetime_points += max(rule.points_delta, 0)
        balance.level = max(1, (balance.lifetime_points // 250) + 1)
        balance.save(update_fields=['total_points', 'lifetime_points', 'level', 'updated_at'])

        badge_awarded = None
        if rule.badge_code:
            badge = BadgeDefinition.objects.filter(code=rule.badge_code, is_active=True).first()
            if badge:
                _, created = UserBadge.objects.get_or_create(
                    user=user,
                    badge=badge,
                    defaults={
                        'source_event_type': event_type,
                        'source_event_id': source_event_id,
                    },
                )
                if created:
                    badge_awarded = badge.code
        return AwardResult(points_delta=rule.points_delta, badge_awarded=badge_awarded, ledger_id=str(ledger.id))
