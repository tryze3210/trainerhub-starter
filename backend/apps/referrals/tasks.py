from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.referrals.models import ReferralInvite, ReferralReward


@shared_task
def process_pending_rewards():
    return ReferralReward.objects.filter(status=ReferralReward.STATUS_PENDING).count()


@shared_task
def expire_invites():
    now = timezone.now()
    qs = ReferralInvite.objects.filter(
        status=ReferralInvite.STATUS_PENDING,
        expires_at__isnull=False,
        expires_at__lt=now,
    )
    updated = qs.update(status=ReferralInvite.STATUS_EXPIRED)
    return updated
