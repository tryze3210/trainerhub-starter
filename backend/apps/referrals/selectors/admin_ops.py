from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.referrals.models import ReferralAttribution, ReferralCode, ReferralInvite, ReferralLedger, ReferralProgram, ReferralReward

MoneyZero = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))


def _sum_money(field_name: str, *, filter_=None):
    return Coalesce(
        Sum(field_name, filter=filter_),
        MoneyZero,
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )


def _money(value: Any) -> str:
    if value is None:
        return "0.00"
    if isinstance(value, Decimal):
        return str(value.quantize(Decimal("0.01")))
    return str(Decimal(str(value)).quantize(Decimal("0.01")))


def _status_rows(model) -> list[dict[str, Any]]:
    return list(model.objects.values("status").annotate(count=Count("id")).order_by("status"))


def _reward_dict(reward: ReferralReward) -> dict[str, Any]:
    attribution = reward.attribution
    invite = attribution.invite
    code = invite.code
    owner = code.owner
    referred_user = attribution.referred_user
    return {
        "id": str(reward.id),
        "status": reward.status,
        "amount": _money(reward.amount),
        "trigger_type": reward.trigger_type,
        "trigger_reference": reward.trigger_reference,
        "program_slug": code.program.slug,
        "code": code.code,
        "owner_id": str(owner.id),
        "owner_email": owner.email,
        "referred_user_id": str(referred_user.id),
        "referred_user_email": referred_user.email,
        "created_at": reward.created_at,
    }


class AdminReferralOpsSelector:
    """Read model for the admin referrals cockpit.

    This selector is intentionally side-effect free. It gives ops/admin UI enough
    data to diagnose attribution, conversion, reward and ledger consistency
    without querying production tables manually.
    """

    @classmethod
    def overview(cls, *, days: int = 30) -> dict[str, Any]:
        days = max(1, min(int(days or 30), 365))
        now = timezone.now()
        since = now - timedelta(days=days)

        invite_counts = _status_rows(ReferralInvite)
        reward_counts = _status_rows(ReferralReward)
        ledger_counts = list(
            ReferralLedger.objects.values("entry_type")
            .annotate(count=Count("id"), amount=_sum_money("amount"))
            .order_by("entry_type")
        )

        reward_totals = ReferralReward.objects.aggregate(
            total_amount=_sum_money("amount"),
            approved_amount=_sum_money("amount", filter_=Q(status=ReferralReward.STATUS_APPROVED)),
            pending_amount=_sum_money("amount", filter_=Q(status=ReferralReward.STATUS_PENDING)),
            rejected_amount=_sum_money("amount", filter_=Q(status=ReferralReward.STATUS_REJECTED)),
            total_count=Count("id"),
            approved_count=Count("id", filter=Q(status=ReferralReward.STATUS_APPROVED)),
            pending_count=Count("id", filter=Q(status=ReferralReward.STATUS_PENDING)),
            rejected_count=Count("id", filter=Q(status=ReferralReward.STATUS_REJECTED)),
        )

        recent_reward_totals = ReferralReward.objects.filter(created_at__gte=since).aggregate(
            amount=_sum_money("amount"),
            count=Count("id"),
        )

        integrity = cls._integrity_snapshot(now=now)
        latest_rewards = [
            _reward_dict(reward)
            for reward in ReferralReward.objects.select_related(
                "attribution__referred_user",
                "attribution__invite__code__owner",
                "attribution__invite__code__program",
            ).order_by("-created_at")[:10]
        ]

        total_invites = ReferralInvite.objects.count()
        converted_invites = ReferralInvite.objects.filter(status=ReferralInvite.STATUS_CONVERTED).count()
        conversion_rate = Decimal("0.00")
        if total_invites:
            conversion_rate = (Decimal(converted_invites) / Decimal(total_invites) * Decimal("100.00")).quantize(
                Decimal("0.01")
            )

        status_value = "warning" if any(integrity.values()) else "healthy"

        return {
            "status": status_value,
            "generated_at": now,
            "range_days": days,
            "summary": {
                "programs": ReferralProgram.objects.count(),
                "active_programs": ReferralProgram.objects.filter(is_active=True).count(),
                "codes": ReferralCode.objects.count(),
                "active_codes": ReferralCode.objects.filter(is_active=True).count(),
                "invites": total_invites,
                "converted_invites": converted_invites,
                "conversion_rate_percent": _money(conversion_rate),
                "attributions": ReferralAttribution.objects.count(),
                "rewards": int(reward_totals.get("total_count") or 0),
                "approved_rewards": int(reward_totals.get("approved_count") or 0),
                "approved_reward_amount": _money(reward_totals.get("approved_amount")),
                "recent_reward_count": int(recent_reward_totals.get("count") or 0),
                "recent_reward_amount": _money(recent_reward_totals.get("amount")),
                "ledger_entries": ReferralLedger.objects.count(),
                "ledger_owners": ReferralLedger.objects.values("owner_id").distinct().count(),
            },
            "invites_by_status": invite_counts,
            "rewards_by_status": reward_counts,
            "reward_totals": {
                "total_amount": _money(reward_totals.get("total_amount")),
                "approved_amount": _money(reward_totals.get("approved_amount")),
                "pending_amount": _money(reward_totals.get("pending_amount")),
                "rejected_amount": _money(reward_totals.get("rejected_amount")),
                "total_count": int(reward_totals.get("total_count") or 0),
                "approved_count": int(reward_totals.get("approved_count") or 0),
                "pending_count": int(reward_totals.get("pending_count") or 0),
                "rejected_count": int(reward_totals.get("rejected_count") or 0),
            },
            "ledger_by_entry_type": [
                {"entry_type": row["entry_type"], "count": row["count"], "amount": _money(row["amount"])}
                for row in ledger_counts
            ],
            "integrity": integrity,
            "latest_rewards": latest_rewards,
        }

    @staticmethod
    def _integrity_snapshot(*, now) -> dict[str, int]:
        stale_pending_invites = ReferralInvite.objects.filter(
            status=ReferralInvite.STATUS_PENDING,
            expires_at__isnull=False,
            expires_at__lt=now,
        ).count()
        converted_without_attribution = ReferralInvite.objects.filter(
            status=ReferralInvite.STATUS_CONVERTED,
            attribution__isnull=True,
        ).count()
        approved_rewards_without_ledger = ReferralReward.objects.filter(
            status=ReferralReward.STATUS_APPROVED,
            ledger_entries__isnull=True,
        ).count()
        rewards_with_multiple_ledger_entries = (
            ReferralReward.objects.annotate(ledger_count=Count("ledger_entries"))
            .filter(ledger_count__gt=1)
            .count()
        )
        ledger_without_reward = ReferralLedger.objects.filter(entry_type=ReferralLedger.ENTRY_REWARD, reward__isnull=True).count()

        return {
            "stale_pending_invites": stale_pending_invites,
            "converted_without_attribution": converted_without_attribution,
            "approved_rewards_without_ledger": approved_rewards_without_ledger,
            "rewards_with_multiple_ledger_entries": rewards_with_multiple_ledger_entries,
            "ledger_reward_entries_without_reward": ledger_without_reward,
        }
