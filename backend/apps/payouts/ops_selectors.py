from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db.models import Count, DecimalField, Min, Max, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet
from apps.payouts.services import ACTIVE_PAYOUT_STATUSES, PayoutService

MONEY_ZERO = Value(Decimal("0.00"), output_field=DecimalField(max_digits=14, decimal_places=2))


def _money_sum(field_name: str):
    return Coalesce(Sum(field_name), MONEY_ZERO, output_field=DecimalField(max_digits=14, decimal_places=2))


def _money(value: Decimal | None) -> str:
    amount = value if value is not None else Decimal("0.00")
    return f"{amount.quantize(Decimal('0.01'))}"


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _parse_dt(value: str):
    value = _clean(value)
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed and timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _parse_limit(value: str | None, *, default: int = 25, maximum: int = 100) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, maximum))


def _apply_trainer_filter(queryset, trainer_id: str, *, prefix: str = ""):
    trainer_id = _clean(trainer_id)
    if not trainer_id:
        return queryset
    return queryset.filter(
        Q(**{f"{prefix}trainer__user_id": trainer_id})
        | Q(**{f"{prefix}trainer_id": trainer_id})
        | Q(**{f"{prefix}trainer__id": trainer_id})
    )


def _apply_created_range(queryset, *, created_from: str, created_to: str):
    start = _parse_dt(created_from)
    end = _parse_dt(created_to)
    if start:
        queryset = queryset.filter(created_at__gte=start)
    if end:
        queryset = queryset.filter(created_at__lte=end)
    return queryset


def _apply_payout_status_filter(queryset, status: str):
    status = _clean(status)
    if not status:
        return queryset
    if status == PayoutRequest.Status.PENDING:
        return queryset.filter(status__in=[PayoutRequest.Status.PENDING, PayoutRequest.Status.REQUESTED])
    return queryset.filter(status=status)


def _normalize_status(status: str) -> str:
    return PayoutRequest.Status.PENDING if status == PayoutRequest.Status.REQUESTED else status


def _status_rows(queryset) -> list[dict[str, Any]]:
    raw_rows = (
        queryset.values("status")
        .annotate(count=Count("id"), amount=_money_sum("amount"))
        .order_by("status")
    )
    merged: dict[str, dict[str, Any]] = {}
    for row in raw_rows:
        status = _normalize_status(row["status"])
        bucket = merged.setdefault(status, {"status": status, "count": 0, "amount": Decimal("0.00")})
        bucket["count"] += row["count"]
        bucket["amount"] += row["amount"] or Decimal("0.00")
    return [
        {"status": row["status"], "count": row["count"], "amount": _money(row["amount"])}
        for row in sorted(merged.values(), key=lambda item: item["status"])
    ]


def _ledger_rows(queryset) -> list[dict[str, Any]]:
    rows = (
        queryset.values("entry_type", "status", "direction")
        .annotate(count=Count("id"), amount=_money_sum("amount"))
        .order_by("entry_type", "status", "direction")
    )
    return [
        {
            "entry_type": row["entry_type"],
            "status": row["status"],
            "direction": row["direction"],
            "count": row["count"],
            "amount": _money(row["amount"]),
        }
        for row in rows
    ]


def _wallet_totals(queryset) -> dict[str, Any]:
    totals = queryset.aggregate(
        trainers_count=Count("id"),
        available_amount=_money_sum("available_amount"),
        pending_amount=_money_sum("pending_amount"),
        locked_amount=_money_sum("locked_amount"),
        oldest_updated_at=Min("updated_at"),
        newest_updated_at=Max("updated_at"),
    )
    return {
        "trainers_count": totals["trainers_count"] or 0,
        "available_amount": _money(totals["available_amount"]),
        "pending_amount": _money(totals["pending_amount"]),
        "locked_amount": _money(totals["locked_amount"]),
        "oldest_updated_at": totals["oldest_updated_at"],
        "newest_updated_at": totals["newest_updated_at"],
    }


def _recent_payouts(queryset, *, limit: int) -> list[dict[str, Any]]:
    rows = queryset.select_related("trainer", "trainer__user", "wallet").order_by("-created_at")[:limit]
    return [
        {
            "id": str(payout.id),
            "trainer_id": str(payout.trainer.user_id),
            "wallet_id": str(payout.wallet_id),
            "status": _normalize_status(payout.status),
            "amount": _money(payout.amount),
            "currency": payout.currency,
            "destination_masked": payout.destination_masked,
            "created_at": payout.created_at,
            "updated_at": payout.updated_at,
        }
        for payout in rows
    ]


def build_admin_payout_ops_summary(params) -> dict[str, Any]:
    status = _clean(params.get("status"))
    trainer_id = _clean(params.get("trainer_id"))
    currency = _clean(params.get("currency"))
    created_from = _clean(params.get("created_from"))
    created_to = _clean(params.get("created_to"))
    limit = _parse_limit(params.get("limit"), default=25, maximum=100)

    payout_queryset = PayoutRequest.objects.select_related("trainer", "trainer__user", "wallet").all()
    payout_queryset = _apply_payout_status_filter(payout_queryset, status)
    payout_queryset = _apply_trainer_filter(payout_queryset, trainer_id)
    payout_queryset = _apply_created_range(payout_queryset, created_from=created_from, created_to=created_to)
    if currency:
        payout_queryset = payout_queryset.filter(currency=currency)

    wallet_queryset = TrainerWallet.objects.select_related("trainer", "trainer__user").all()
    wallet_queryset = _apply_trainer_filter(wallet_queryset, trainer_id)
    if currency:
        wallet_queryset = wallet_queryset.filter(currency=currency)

    ledger_queryset = BalanceEntry.objects.select_related("wallet", "wallet__trainer", "wallet__trainer__user").all()
    if trainer_id:
        ledger_queryset = ledger_queryset.filter(
            Q(wallet__trainer__user_id=trainer_id)
            | Q(wallet__trainer_id=trainer_id)
            | Q(wallet__trainer__id=trainer_id)
        )
    ledger_queryset = _apply_created_range(ledger_queryset, created_from=created_from, created_to=created_to)
    if currency:
        ledger_queryset = ledger_queryset.filter(currency=currency)

    active_statuses = set(ACTIVE_PAYOUT_STATUSES)
    active_queryset = payout_queryset.filter(status__in=active_statuses)
    active_totals = active_queryset.aggregate(count=Count("id"), amount=_money_sum("amount"))
    payout_totals = payout_queryset.aggregate(
        count=Count("id"),
        amount=_money_sum("amount"),
        oldest_created_at=Min("created_at"),
        newest_created_at=Max("created_at"),
    )
    ledger_totals = ledger_queryset.aggregate(count=Count("id"), amount=_money_sum("amount"))

    reconciliation = PayoutService.build_reconciliation_report()

    return {
        "generated_at": timezone.now(),
        "filters": {
            "status": status,
            "trainer_id": trainer_id,
            "currency": currency,
            "created_from": created_from,
            "created_to": created_to,
            "limit": limit,
        },
        "summary": {
            "total_payout_requests": payout_totals["count"] or 0,
            "total_payout_amount": _money(payout_totals["amount"]),
            "active_payout_count": active_totals["count"] or 0,
            "active_payout_amount": _money(active_totals["amount"]),
            "ledger_entry_count": ledger_totals["count"] or 0,
            "ledger_entry_amount": _money(ledger_totals["amount"]),
            "oldest_payout_created_at": payout_totals["oldest_created_at"],
            "newest_payout_created_at": payout_totals["newest_created_at"],
        },
        "wallets": _wallet_totals(wallet_queryset),
        "payout_statuses": _status_rows(payout_queryset),
        "ledger": _ledger_rows(ledger_queryset),
        "reconciliation": {
            "status": reconciliation.get("status", "unknown"),
            "issue_count": reconciliation.get("issue_count", 0),
            "checked_at": reconciliation.get("checked_at", ""),
        },
        "recent_payouts": _recent_payouts(payout_queryset, limit=limit),
    }

# Backward-compatible public name used by payouts admin-ops API views/tests.
def build_payout_admin_ops_summary(params) -> dict[str, Any]:
    return build_admin_payout_ops_summary(params)
