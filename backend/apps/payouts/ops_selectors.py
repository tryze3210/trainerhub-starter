from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db.models import Count, DecimalField, Min, Max, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.legal_compliance.services.eligibility import PayoutEligibilityService
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


def _payout_eligibility_payload(payout: PayoutRequest) -> dict[str, Any]:
    result = PayoutEligibilityService.evaluate_for_trainer(payout.trainer.user)
    return {
        "is_eligible": result.is_eligible,
        "block_reason": result.block_reason,
        "has_active_agreement": result.has_active_agreement,
        "has_verified_payout_profile": result.has_verified_payout_profile,
        "kyc_status": result.kyc_status,
    }


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
            "payout_eligibility": _payout_eligibility_payload(payout),
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


def _issue(*, code: str, severity: str, message: str, **context: Any) -> dict[str, Any]:
    payload = {
        "code": code,
        "severity": severity,
        "message": message,
    }
    payload.update(context)
    return payload


def _payout_filter_queryset(params):
    status = _clean(params.get("status"))
    trainer_id = _clean(params.get("trainer_id"))
    currency = _clean(params.get("currency"))
    created_from = _clean(params.get("created_from"))
    created_to = _clean(params.get("created_to"))

    queryset = PayoutRequest.objects.select_related("trainer", "trainer__user", "wallet").all()
    queryset = _apply_payout_status_filter(queryset, status)
    queryset = _apply_trainer_filter(queryset, trainer_id)
    queryset = _apply_created_range(queryset, created_from=created_from, created_to=created_to)
    if currency:
        queryset = queryset.filter(currency=currency.upper())
    return queryset


def _ledger_filter_queryset(params):
    trainer_id = _clean(params.get("trainer_id"))
    currency = _clean(params.get("currency"))
    created_from = _clean(params.get("created_from"))
    created_to = _clean(params.get("created_to"))
    entry_type = _clean(params.get("entry_type"))
    direction = _clean(params.get("direction"))
    source_type = _clean(params.get("source_type"))

    queryset = BalanceEntry.objects.select_related("wallet", "wallet__trainer", "wallet__trainer__user").all()
    if trainer_id:
        queryset = queryset.filter(
            Q(wallet__trainer__user_id=trainer_id)
            | Q(wallet__trainer_id=trainer_id)
            | Q(wallet__trainer__id=trainer_id)
        )
    queryset = _apply_created_range(queryset, created_from=created_from, created_to=created_to)
    if currency:
        queryset = queryset.filter(currency=currency.upper())
    if entry_type:
        queryset = queryset.filter(entry_type=entry_type)
    if direction:
        queryset = queryset.filter(direction=direction)
    if source_type:
        queryset = queryset.filter(source_type=source_type)
    return queryset


def _wallet_filter_queryset(params):
    trainer_id = _clean(params.get("trainer_id"))
    currency = _clean(params.get("currency"))
    queryset = TrainerWallet.objects.select_related("trainer", "trainer__user").all()
    queryset = _apply_trainer_filter(queryset, trainer_id)
    if currency:
        queryset = queryset.filter(currency=currency.upper())
    return queryset


def _active_payout_totals_by_wallet(params) -> dict[str, dict[str, Any]]:
    trainer_id = _clean(params.get("trainer_id"))
    currency = _clean(params.get("currency"))
    queryset = PayoutRequest.objects.filter(status__in=ACTIVE_PAYOUT_STATUSES)
    queryset = _apply_trainer_filter(queryset, trainer_id)
    if currency:
        queryset = queryset.filter(currency=currency.upper())

    rows = queryset.values("wallet_id").annotate(count=Count("id"), amount=_money_sum("amount"))
    return {
        str(row["wallet_id"]): {
            "count": row["count"] or 0,
            "amount": row["amount"] or Decimal("0.00"),
        }
        for row in rows
    }


def _serialize_integrity_issue(issue: dict[str, Any]) -> dict[str, Any]:
    serialized: dict[str, Any] = {}
    for key, value in issue.items():
        if isinstance(value, Decimal):
            serialized[key] = _money(value)
        elif isinstance(value, list):
            serialized[key] = [str(item) for item in value]
        else:
            serialized[key] = value
    return serialized


def build_payout_integrity_snapshot(params) -> dict[str, Any]:
    """Return a read-only integrity snapshot for payout wallet/request/ledger consistency."""
    status = _clean(params.get("status"))
    trainer_id = _clean(params.get("trainer_id"))
    currency = _clean(params.get("currency"))
    created_from = _clean(params.get("created_from"))
    created_to = _clean(params.get("created_to"))
    limit = _parse_limit(params.get("limit"), default=100, maximum=500)

    issues: list[dict[str, Any]] = []
    wallets = list(_wallet_filter_queryset(params).order_by("trainer_id", "currency", "id"))
    payouts = list(_payout_filter_queryset(params).order_by("-created_at")[:1000])
    payout_ids = {payout.id for payout in payouts}
    payout_by_id = {str(payout.id): payout for payout in payouts}
    ledger_queryset = _ledger_filter_queryset(params)
    ledger_entries = list(ledger_queryset.order_by("-created_at")[:2000])
    active_by_wallet = _active_payout_totals_by_wallet(params)

    for wallet in wallets:
        wallet_id = str(wallet.id)
        active = active_by_wallet.get(wallet_id, {"count": 0, "amount": Decimal("0.00")})
        active_amount = active["amount"]
        delta = wallet.locked_amount - active_amount
        if wallet.available_amount < Decimal("0.00"):
            issues.append(
                _issue(
                    code="negative_available_balance",
                    severity="critical",
                    message="Trainer wallet available balance is negative.",
                    trainer_id=str(wallet.trainer.user_id),
                    wallet_id=wallet_id,
                    currency=wallet.currency,
                    available_amount=wallet.available_amount,
                    locked_amount=wallet.locked_amount,
                    delta=wallet.available_amount,
                )
            )
        if wallet.locked_amount < Decimal("0.00"):
            issues.append(
                _issue(
                    code="negative_locked_balance",
                    severity="critical",
                    message="Trainer wallet locked balance is negative.",
                    trainer_id=str(wallet.trainer.user_id),
                    wallet_id=wallet_id,
                    currency=wallet.currency,
                    available_amount=wallet.available_amount,
                    locked_amount=wallet.locked_amount,
                    delta=wallet.locked_amount,
                )
            )
        if delta != Decimal("0.00"):
            issues.append(
                _issue(
                    code="locked_balance_mismatch",
                    severity="high",
                    message="Wallet locked balance does not match the sum of active payout requests.",
                    trainer_id=str(wallet.trainer.user_id),
                    wallet_id=wallet_id,
                    currency=wallet.currency,
                    locked_amount=wallet.locked_amount,
                    active_payout_amount=active_amount,
                    active_payout_count=active["count"],
                    delta=delta,
                )
            )

    reserve_by_payout: dict[str, list[BalanceEntry]] = {}
    payout_by_payout: dict[str, list[BalanceEntry]] = {}
    release_by_payout: dict[str, list[BalanceEntry]] = {}
    for entry in ledger_entries:
        if entry.source_type != "payout_request":
            continue
        key = str(entry.source_id)
        if entry.entry_type == BalanceEntry.EntryType.RESERVE:
            reserve_by_payout.setdefault(key, []).append(entry)
        if entry.entry_type == BalanceEntry.EntryType.PAYOUT:
            payout_by_payout.setdefault(key, []).append(entry)
        if entry.entry_type == BalanceEntry.EntryType.RELEASE:
            release_by_payout.setdefault(key, []).append(entry)

    for payout in payouts:
        payout_id = str(payout.id)
        canonical_status = _normalize_status(payout.status)
        reserves = reserve_by_payout.get(payout_id, [])
        payout_entries = payout_by_payout.get(payout_id, [])
        release_entries = release_by_payout.get(payout_id, [])

        if payout.wallet_id and payout.wallet.currency != payout.currency:
            issues.append(
                _issue(
                    code="payout_wallet_currency_mismatch",
                    severity="high",
                    message="Payout currency differs from its wallet currency.",
                    payout_id=payout_id,
                    trainer_id=str(payout.trainer.user_id),
                    wallet_id=str(payout.wallet_id),
                    payout_currency=payout.currency,
                    wallet_currency=payout.wallet.currency,
                    amount=payout.amount,
                )
            )

        if canonical_status in ACTIVE_PAYOUT_STATUSES:
            if not reserves:
                issues.append(
                    _issue(
                        code="active_payout_missing_reserve_ledger",
                        severity="high",
                        message="Active payout request has no reserve ledger entry.",
                        payout_id=payout_id,
                        trainer_id=str(payout.trainer.user_id),
                        wallet_id=str(payout.wallet_id),
                        status=canonical_status,
                        amount=payout.amount,
                        currency=payout.currency,
                    )
                )
            if len(reserves) > 1:
                issues.append(
                    _issue(
                        code="duplicate_payout_reserve_ledger",
                        severity="high",
                        message="Payout request has multiple reserve ledger entries.",
                        payout_id=payout_id,
                        trainer_id=str(payout.trainer.user_id),
                        wallet_id=str(payout.wallet_id),
                        status=canonical_status,
                        reserve_entry_count=len(reserves),
                        amount=payout.amount,
                        currency=payout.currency,
                    )
                )
            reserve_amount = sum((entry.amount for entry in reserves), Decimal("0.00"))
            if reserves and reserve_amount != payout.amount:
                issues.append(
                    _issue(
                        code="payout_reserve_amount_mismatch",
                        severity="medium",
                        message="Reserve ledger amount does not match payout amount.",
                        payout_id=payout_id,
                        trainer_id=str(payout.trainer.user_id),
                        wallet_id=str(payout.wallet_id),
                        status=canonical_status,
                        reserve_amount=reserve_amount,
                        payout_amount=payout.amount,
                        delta=reserve_amount - payout.amount,
                        currency=payout.currency,
                    )
                )
        if payout.status == PayoutRequest.Status.PAID and not payout_entries:
            issues.append(
                _issue(
                    code="paid_payout_missing_payout_ledger",
                    severity="high",
                    message="Paid payout has no payout ledger entry.",
                    payout_id=payout_id,
                    trainer_id=str(payout.trainer.user_id),
                    wallet_id=str(payout.wallet_id),
                    amount=payout.amount,
                    currency=payout.currency,
                )
            )
        if payout.status == PayoutRequest.Status.REJECTED and not release_entries:
            issues.append(
                _issue(
                    code="rejected_payout_missing_release_ledger",
                    severity="medium",
                    message="Rejected payout has no release ledger entry.",
                    payout_id=payout_id,
                    trainer_id=str(payout.trainer.user_id),
                    wallet_id=str(payout.wallet_id),
                    amount=payout.amount,
                    currency=payout.currency,
                )
            )

    for entry in ledger_entries:
        if entry.amount < Decimal("0.00"):
            issues.append(
                _issue(
                    code="negative_ledger_amount",
                    severity="critical",
                    message="Payout ledger entry amount is negative.",
                    ledger_entry_id=str(entry.id),
                    wallet_id=str(entry.wallet_id),
                    trainer_id=str(entry.wallet.trainer.user_id),
                    entry_type=entry.entry_type,
                    direction=entry.direction,
                    amount=entry.amount,
                    currency=entry.currency,
                )
            )
        if entry.currency != entry.wallet.currency:
            issues.append(
                _issue(
                    code="ledger_wallet_currency_mismatch",
                    severity="medium",
                    message="Ledger entry currency differs from wallet currency.",
                    ledger_entry_id=str(entry.id),
                    wallet_id=str(entry.wallet_id),
                    trainer_id=str(entry.wallet.trainer.user_id),
                    entry_currency=entry.currency,
                    wallet_currency=entry.wallet.currency,
                    amount=entry.amount,
                )
            )
        if entry.source_type == "payout_request":
            payout = payout_by_id.get(str(entry.source_id))
            if not payout:
                payout = (
                    PayoutRequest.objects.select_related("trainer", "wallet")
                    .filter(id=entry.source_id)
                    .first()
                )
            if not payout:
                issues.append(
                    _issue(
                        code="orphan_payout_ledger_entry",
                        severity="high",
                        message="Ledger entry references a missing payout request.",
                        ledger_entry_id=str(entry.id),
                        wallet_id=str(entry.wallet_id),
                        trainer_id=str(entry.wallet.trainer.user_id),
                        source_id=str(entry.source_id),
                        entry_type=entry.entry_type,
                        amount=entry.amount,
                        currency=entry.currency,
                    )
                )
                continue
            if payout and entry.wallet_id != payout.wallet_id:
                issues.append(
                    _issue(
                        code="ledger_payout_wallet_mismatch",
                        severity="high",
                        message="Ledger entry wallet differs from referenced payout wallet.",
                        ledger_entry_id=str(entry.id),
                        payout_id=str(payout.id),
                        ledger_wallet_id=str(entry.wallet_id),
                        payout_wallet_id=str(payout.wallet_id),
                        amount=entry.amount,
                        currency=entry.currency,
                    )
                )
            if payout and entry.currency != payout.currency:
                issues.append(
                    _issue(
                        code="ledger_payout_currency_mismatch",
                        severity="medium",
                        message="Ledger entry currency differs from referenced payout currency.",
                        ledger_entry_id=str(entry.id),
                        payout_id=str(payout.id),
                        ledger_currency=entry.currency,
                        payout_currency=payout.currency,
                        amount=entry.amount,
                    )
                )

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda item: (severity_order.get(item["severity"], 9), item["code"]))
    issue_codes: dict[str, int] = {}
    issue_severities: dict[str, int] = {}
    for issue in issues:
        issue_codes[issue["code"]] = issue_codes.get(issue["code"], 0) + 1
        issue_severities[issue["severity"]] = issue_severities.get(issue["severity"], 0) + 1

    return {
        "generated_at": timezone.now(),
        "mode": "read_only_integrity_snapshot",
        "filters": {
            "status": status,
            "trainer_id": trainer_id,
            "currency": currency.upper() if currency else "",
            "created_from": created_from,
            "created_to": created_to,
            "limit": limit,
        },
        "summary": {
            "status": "healthy" if not issues else "attention_required",
            "issue_count": len(issues),
            "wallet_count": len(wallets),
            "payouts_scanned": len(payouts),
            "ledger_entries_scanned": len(ledger_entries),
            "truncated": len(issues) > limit,
        },
        "issue_codes": issue_codes,
        "issue_severities": issue_severities,
        "issues": [_serialize_integrity_issue(issue) for issue in issues[:limit]],
        "actions": {
            "repair_performed": False,
            "note": "This endpoint is read-only. It does not mutate payout requests, wallets or ledger entries.",
        },
    }


def _decimal_from_issue(issue: dict[str, Any], key: str) -> Decimal:
    try:
        return Decimal(str(issue.get(key, "0.00") or "0.00"))
    except Exception:
        return Decimal("0.00")


def _repair_preview_action(issue: dict[str, Any]) -> dict[str, Any]:
    code = str(issue.get("code", ""))
    severity = str(issue.get("severity", "medium"))
    base: dict[str, Any] = {
        "issue_code": code,
        "severity": severity,
        "payout_id": issue.get("payout_id", ""),
        "wallet_id": issue.get("wallet_id", ""),
        "trainer_id": issue.get("trainer_id", ""),
        "currency": issue.get("currency", issue.get("payout_currency", issue.get("wallet_currency", ""))),
        "requires_confirmation": True,
        "dry_run_only": True,
    }

    if code == "locked_balance_mismatch":
        delta = _decimal_from_issue(issue, "delta")
        available_amount = _decimal_from_issue(issue, "available_amount")
        if delta > Decimal("0.00"):
            return {
                **base,
                "action_code": "release_excess_locked_to_available",
                "eligible_for_auto_repair": True,
                "risk_level": "medium",
                "amount": _money(delta),
                "message": "Preview: release excess locked balance back to available balance.",
            }
        missing_locked = abs(delta)
        can_lock_available = available_amount >= missing_locked
        return {
            **base,
            "action_code": "move_available_to_locked" if can_lock_available else "manual_review_insufficient_available_to_lock",
            "eligible_for_auto_repair": bool(can_lock_available),
            "risk_level": "high" if can_lock_available else "critical",
            "amount": _money(missing_locked),
            "message": (
                "Preview: move available balance to locked balance."
                if can_lock_available
                else "Manual review required: wallet does not have enough available balance to cover missing locked amount."
            ),
        }

    if code == "active_payout_missing_reserve_ledger":
        return {
            **base,
            "action_code": "create_missing_reserve_ledger",
            "eligible_for_auto_repair": True,
            "risk_level": "medium",
            "amount": issue.get("amount", "0.00"),
            "message": "Preview: create missing reserve ledger entry for active payout request.",
        }

    if code == "paid_payout_missing_payout_ledger":
        return {
            **base,
            "action_code": "create_missing_payout_ledger",
            "eligible_for_auto_repair": False,
            "risk_level": "high",
            "amount": issue.get("amount", "0.00"),
            "message": "Manual approval required: paid payout is missing payout ledger evidence.",
        }

    if code == "rejected_payout_missing_release_ledger":
        return {
            **base,
            "action_code": "create_missing_release_ledger",
            "eligible_for_auto_repair": False,
            "risk_level": "high",
            "amount": issue.get("amount", "0.00"),
            "message": "Manual approval required: rejected payout is missing release ledger evidence.",
        }

    return {
        **base,
        "action_code": "manual_review_required",
        "eligible_for_auto_repair": False,
        "risk_level": "critical" if severity == "critical" else "high",
        "amount": issue.get("amount", issue.get("delta", "0.00")),
        "message": "Manual review required. This issue is not eligible for automatic repair.",
    }


def build_payout_repair_preview(params) -> dict[str, Any]:
    """Return a dry-run payout repair plan derived from the read-only integrity snapshot."""
    status = _clean(params.get("status"))
    trainer_id = _clean(params.get("trainer_id"))
    currency = _clean(params.get("currency"))
    created_from = _clean(params.get("created_from"))
    created_to = _clean(params.get("created_to"))
    batch_size = _parse_limit(params.get("batch_size") or params.get("limit"), default=25, maximum=100)

    snapshot_params = {
        "status": status,
        "trainer_id": trainer_id,
        "currency": currency,
        "created_from": created_from,
        "created_to": created_to,
        "limit": max(batch_size, 100),
    }
    snapshot = build_payout_integrity_snapshot(snapshot_params)
    issues = list(snapshot.get("issues") or [])
    selected_issues = issues[:batch_size]
    actions = [_repair_preview_action(issue) for issue in selected_issues]
    auto_repairable_count = sum(1 for action in actions if action.get("eligible_for_auto_repair"))
    action_codes: dict[str, int] = {}
    for action in actions:
        code = str(action.get("action_code", "manual_review_required"))
        action_codes[code] = action_codes.get(code, 0) + 1

    return {
        "generated_at": timezone.now(),
        "mode": "dry_run_repair_preview",
        "deletion_performed": False,
        "repair_performed": False,
        "filters": {
            "status": status,
            "trainer_id": trainer_id,
            "currency": currency.upper() if currency else "",
            "created_from": created_from,
            "created_to": created_to,
            "batch_size": batch_size,
        },
        "summary": {
            "status": snapshot.get("summary", {}).get("status", "unknown"),
            "issue_count": snapshot.get("summary", {}).get("issue_count", 0),
            "preview_count": len(actions),
            "auto_repairable_count": auto_repairable_count,
            "manual_review_count": len(actions) - auto_repairable_count,
            "has_more": len(issues) > batch_size,
        },
        "action_codes": action_codes,
        "actions": actions,
        "integrity": {
            "issue_codes": snapshot.get("issue_codes", {}),
            "issue_severities": snapshot.get("issue_severities", {}),
        },
        "safety": {
            "dry_run_only": True,
            "requires_confirmation_for_future_execution": True,
            "note": "This endpoint is read-only. It does not mutate payout requests, wallets or ledger entries.",
        },
    }
