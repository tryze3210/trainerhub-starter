from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.conf import settings
from django.utils import timezone

from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet
from apps.trainers.models import TrainerProfile

ZERO = Decimal("0.00")
MONEY_QUANT = Decimal("0.01")

SALE_ENTRY_TYPES = {"sale_credit", "accrual", "subscription_credit"}
REFUND_ENTRY_TYPES = {"refund_debit", "refund", "reversal"}
CHARGEBACK_ENTRY_TYPES = {"chargeback_debit", "chargeback"}
PAYOUT_ENTRY_TYPES = {"payout", "payout_debit"}
PENDING_PAYOUT_STATUSES = {
    getattr(PayoutRequest.Status, "REQUESTED", "requested"),
    getattr(PayoutRequest.Status, "PENDING", "pending"),
    getattr(PayoutRequest.Status, "APPROVED", "approved"),
    getattr(PayoutRequest.Status, "PROCESSING", "processing"),
}
PAID_PAYOUT_STATUSES = {getattr(PayoutRequest.Status, "PAID", "paid")}


class TrainerRevenueAccessError(Exception):
    """Raised when the authenticated user does not have a trainer revenue scope."""


def _money(value: Decimal | int | str | None) -> str:
    amount = Decimal(value or ZERO).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
    return f"{amount:.2f}"


def _decimal(value: Decimal | int | str | None) -> Decimal:
    return Decimal(value or ZERO).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def _direction(entry: BalanceEntry) -> str:
    return str(getattr(entry, "direction", "") or "").lower()


def _entry_type(entry: BalanceEntry) -> str:
    return str(getattr(entry, "entry_type", "") or "").lower()


def _is_credit(entry: BalanceEntry) -> bool:
    return _direction(entry) == "credit"


def _is_debit(entry: BalanceEntry) -> bool:
    return _direction(entry) == "debit"


def _commission_rate() -> Decimal:
    raw = getattr(settings, "TRAINERHUB_DEFAULT_PLATFORM_COMMISSION_RATE", None)
    if raw is None:
        raw = getattr(settings, "GLOBAL_COMMISSION_RATE", Decimal("20.00"))
    rate = Decimal(str(raw))
    if rate > 1:
        rate = rate / Decimal("100.00")
    if rate < 0 or rate >= 1:
        return Decimal("0.20")
    return rate.quantize(Decimal("0.0001"))


def _trainer_profile_for_user(user: Any) -> TrainerProfile:
    profile = (
        TrainerProfile.objects.select_related("user")
        .filter(user_id=getattr(user, "id", None))
        .first()
    )
    if profile is None:
        raise TrainerRevenueAccessError("Trainer profile was not found for the current user.")
    return profile


def _wallet_for_profile(profile: TrainerProfile) -> TrainerWallet | None:
    try:
        return profile.wallet
    except TrainerWallet.DoesNotExist:
        return None


def _safe_iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _wallet_payload(wallet: TrainerWallet | None, currency: str) -> dict[str, str]:
    if wallet is None:
        return {
            "currency": currency,
            "available_amount": _money(ZERO),
            "pending_amount": _money(ZERO),
            "reserved_amount": _money(ZERO),
            "locked_amount": _money(ZERO),
            "lifetime_earned": _money(ZERO),
        }

    return {
        "currency": wallet.currency,
        "available_amount": _money(getattr(wallet, "available_amount", ZERO)),
        "pending_amount": _money(getattr(wallet, "pending_amount", ZERO)),
        "reserved_amount": _money(getattr(wallet, "reserved_amount", getattr(wallet, "locked_amount", ZERO))),
        "locked_amount": _money(getattr(wallet, "locked_amount", ZERO)),
        "lifetime_earned": _money(getattr(wallet, "lifetime_earned_amount", getattr(wallet, "lifetime_earned", ZERO))),
    }


def _entry_queryset(wallet: TrainerWallet, *, since=None):
    queryset = BalanceEntry.objects.filter(wallet=wallet).order_by("-created_at", "-id")
    if since is not None:
        queryset = queryset.filter(created_at__gte=since)
    return queryset


def _entry_description(entry: BalanceEntry) -> str:
    metadata = getattr(entry, "metadata", None) or {}
    if isinstance(metadata, dict):
        return str(metadata.get("description") or metadata.get("reason") or "")
    return ""


def _entry_payload(entry: BalanceEntry) -> dict[str, Any]:
    return {
        "id": str(entry.id),
        "created_at": _safe_iso(getattr(entry, "created_at", None)),
        "entry_type": entry.entry_type,
        "direction": entry.direction,
        "amount": _money(entry.amount),
        "currency": entry.currency,
        "status": entry.status,
        "source_type": entry.source_type,
        "source_id": str(entry.source_id) if entry.source_id else None,
        "description": _entry_description(entry),
        "metadata": getattr(entry, "metadata", {}) or {},
    }


def _payout_payload(request: PayoutRequest) -> dict[str, Any]:
    metadata = getattr(request, "metadata", None) or getattr(request, "destination_json", {}) or {}
    return {
        "id": str(request.id),
        "created_at": _safe_iso(getattr(request, "created_at", None)),
        "updated_at": _safe_iso(getattr(request, "updated_at", None)),
        "requested_at": _safe_iso(getattr(request, "requested_at", None)),
        "approved_at": _safe_iso(getattr(request, "approved_at", None)),
        "processed_at": _safe_iso(getattr(request, "processed_at", None)),
        "amount": _money(request.amount),
        "currency": request.currency,
        "status": request.status,
        "destination_masked": getattr(request, "destination_masked", ""),
        "rejected_reason": getattr(request, "rejected_reason", ""),
        "destination_json": getattr(request, "destination_json", {}) or {},
        "metadata": metadata,
    }


def build_trainer_revenue_summary(*, user: Any, days: int = 30) -> dict[str, Any]:
    profile = _trainer_profile_for_user(user)
    wallet = _wallet_for_profile(profile)
    currency = wallet.currency if wallet else "RUB"
    now = timezone.now()
    since = now - timedelta(days=days)
    entries = list(_entry_queryset(wallet, since=since)) if wallet else []

    net_sales = ZERO
    refunds = ZERO
    chargebacks = ZERO
    payout_debits = ZERO
    by_source: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "source_type": "unknown",
            "source_id": None,
            "net_revenue": ZERO,
            "transaction_count": 0,
        }
    )

    for entry in entries:
        entry_type = _entry_type(entry)
        amount = _decimal(entry.amount)

        if _is_credit(entry) and entry_type in SALE_ENTRY_TYPES:
            net_sales += amount
            source_key = f"{entry.source_type or 'unknown'}:{entry.source_id or 'none'}"
            bucket = by_source[source_key]
            bucket["source_type"] = entry.source_type or "unknown"
            bucket["source_id"] = str(entry.source_id) if entry.source_id else None
            bucket["net_revenue"] += amount
            bucket["transaction_count"] += 1
            continue

        if _is_debit(entry) and entry_type in REFUND_ENTRY_TYPES:
            refunds += amount
            continue

        if _is_debit(entry) and entry_type in CHARGEBACK_ENTRY_TYPES:
            chargebacks += amount
            continue

        if _is_debit(entry) and entry_type in PAYOUT_ENTRY_TYPES:
            payout_debits += amount

    commission_rate = _commission_rate()
    if net_sales > 0 and commission_rate < 1:
        estimated_gross_sales = (net_sales / (Decimal("1.00") - commission_rate)).quantize(
            MONEY_QUANT,
            rounding=ROUND_HALF_UP,
        )
    else:
        estimated_gross_sales = ZERO
    estimated_platform_commission = max(estimated_gross_sales - net_sales, ZERO)

    payout_requests = list(PayoutRequest.objects.filter(trainer=profile).order_by("-created_at", "-id"))
    pending_payout_requests = sum(
        (_decimal(item.amount) for item in payout_requests if item.status in PENDING_PAYOUT_STATUSES),
        ZERO,
    )
    paid_payout_requests = sum(
        (_decimal(item.amount) for item in payout_requests if item.status in PAID_PAYOUT_STATUSES),
        ZERO,
    )

    source_rows = sorted(by_source.values(), key=lambda item: item["net_revenue"], reverse=True)
    top_sources = [
        {
            "source_type": item["source_type"],
            "source_id": item["source_id"],
            "net_revenue": _money(item["net_revenue"]),
            "transaction_count": item["transaction_count"],
        }
        for item in source_rows[:10]
    ]

    wallet_payload = _wallet_payload(wallet, currency)
    return {
        "period": {
            "days": days,
            "since": since.isoformat(),
            "until": now.isoformat(),
        },
        "trainer": {
            "id": str(profile.id),
            "slug": profile.slug,
            "display_name": profile.display_name,
            "status": profile.status,
        },
        "currency": currency,
        "wallet": wallet_payload,
        "revenue": {
            "gross_sales": _money(estimated_gross_sales),
            "platform_commission": _money(estimated_platform_commission),
            "net_revenue": _money(net_sales),
            "refunds": _money(refunds),
            "chargebacks": _money(chargebacks),
            "paid_out": _money(paid_payout_requests or payout_debits),
            "pending_payout": _money(pending_payout_requests),
            "available_payout": wallet_payload["available_amount"],
            "reserved_balance": wallet_payload["reserved_amount"],
        },
        "counts": {
            "transactions": len(entries),
            "payout_requests": len(payout_requests),
            "paid_payouts": len([item for item in payout_requests if item.status in PAID_PAYOUT_STATUSES]),
        },
        "top_sources": top_sources,
        "notes": [
            "gross_sales and platform_commission are estimated from trainer net ledger entries when provider price snapshots are not attached to the payout ledger.",
        ],
    }


def list_trainer_revenue_transactions(*, user: Any, limit: int = 100) -> dict[str, Any]:
    profile = _trainer_profile_for_user(user)
    wallet = _wallet_for_profile(profile)
    currency = wallet.currency if wallet else "RUB"
    entries = list(_entry_queryset(wallet)[:limit]) if wallet else []
    return {
        "trainer": {
            "id": str(profile.id),
            "slug": profile.slug,
            "display_name": profile.display_name,
        },
        "currency": currency,
        "limit": limit,
        "count": len(entries),
        "results": [_entry_payload(entry) for entry in entries],
    }


def list_trainer_revenue_payouts(*, user: Any, limit: int = 100) -> dict[str, Any]:
    profile = _trainer_profile_for_user(user)
    payouts = list(PayoutRequest.objects.filter(trainer=profile).order_by("-created_at", "-id")[:limit])
    return {
        "trainer": {
            "id": str(profile.id),
            "slug": profile.slug,
            "display_name": profile.display_name,
        },
        "limit": limit,
        "count": len(payouts),
        "results": [_payout_payload(item) for item in payouts],
    }
