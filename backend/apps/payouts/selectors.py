from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce

from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet
from apps.payouts.services import PayoutService
from apps.trainers.models import TrainerProfile


MONEY_ZERO = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))


def _money_sum(field_name: str):
    return Coalesce(Sum(field_name), MONEY_ZERO, output_field=DecimalField(max_digits=14, decimal_places=2))


def _uuid_or_none(value):
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _trainer_profile_filter(trainer_id):
    uid = _uuid_or_none(trainer_id)
    if not uid:
        return Q(pk__isnull=True)
    return Q(user_id=uid) | Q(id=uid)


def get_balance_for_trainer(trainer_id):
    return TrainerWallet.objects.select_related("trainer", "trainer__user").filter(
        trainer__in=TrainerProfile.objects.filter(_trainer_profile_filter(trainer_id))
    ).first()


def list_payout_requests_for_trainer(trainer_id):
    return (
        PayoutRequest.objects.select_related("trainer", "trainer__user", "wallet")
        .filter(trainer__in=TrainerProfile.objects.filter(_trainer_profile_filter(trainer_id)))
        .order_by("-created_at")
    )


def list_all_payout_requests():
    return PayoutRequest.objects.select_related("trainer", "trainer__user", "wallet").all().order_by("-created_at")


def get_admin_payout_operations_overview() -> dict:
    status_rows = (
        PayoutRequest.objects.values("status")
        .annotate(count=Count("id"), amount=_money_sum("amount"))
        .order_by("status")
    )
    ledger_rows = (
        BalanceEntry.objects.values("entry_type")
        .annotate(count=Count("id"), amount=_money_sum("amount"))
        .order_by("entry_type")
    )
    wallet_totals = TrainerWallet.objects.aggregate(
        available_amount=_money_sum("available_amount"),
        reserved_amount=_money_sum("locked_amount"),
        pending_amount=_money_sum("pending_amount"),
        trainers_count=Count("id"),
    )
    lifetime = BalanceEntry.objects.filter(direction="credit").aggregate(
        amount=_money_sum("amount"),
    )["amount"]
    balance_totals = {
        "available_amount": wallet_totals["available_amount"] or Decimal("0.00"),
        "reserved_amount": wallet_totals["reserved_amount"] or Decimal("0.00"),
        "lifetime_earned_amount": lifetime or Decimal("0.00"),
        "trainers_count": wallet_totals["trainers_count"] or 0,
    }

    status_map = {row["status"]: {"count": row["count"], "amount": row["amount"]} for row in status_rows}
    operational_statuses = [
        PayoutRequest.Status.REQUESTED,
        PayoutRequest.Status.PENDING,
        PayoutRequest.Status.APPROVED,
        PayoutRequest.Status.PROCESSING,
    ]

    pending_exposure = sum(
        (status_map.get(item, {}).get("amount") or Decimal("0.00") for item in operational_statuses),
        Decimal("0.00"),
    )
    pending_count = sum((status_map.get(item, {}).get("count") or 0 for item in operational_statuses), 0)
    reconciliation = PayoutService.build_reconciliation_report()

    normalized_statuses = []
    for row in status_rows:
        status = PayoutRequest.Status.PENDING if row["status"] == PayoutRequest.Status.REQUESTED else row["status"]
        existing = next((item for item in normalized_statuses if item["status"] == status), None)
        if existing:
            existing["count"] += row["count"]
            existing["amount"] += row["amount"]
        else:
            normalized_statuses.append({"status": status, "count": row["count"], "amount": row["amount"]})

    return {
        "statuses": normalized_statuses,
        "ledger": [
            {"entry_type": row["entry_type"], "count": row["count"], "amount": row["amount"]}
            for row in ledger_rows
        ],
        "balances": balance_totals,
        "ops": {
            "pending_exposure_amount": pending_exposure,
            "pending_exposure_count": pending_count,
            "reserved_amount": balance_totals["reserved_amount"],
            "available_amount": balance_totals["available_amount"],
            "reconciliation_status": reconciliation["status"],
            "reconciliation_issue_count": reconciliation["issue_count"],
        },
        "recent_requests": list_all_payout_requests()[:10],
    }
