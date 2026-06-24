from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet
from apps.payouts.ops_selectors import build_payout_integrity_snapshot, build_payout_repair_preview
from apps.payouts.services import ACTIVE_PAYOUT_STATUSES


SAFE_AUTO_REPAIR_ISSUE_CODES = {
    "locked_balance_mismatch",
    "active_payout_missing_reserve_ledger",
    "rejected_payout_missing_release_ledger",
}

MANUAL_REVIEW_ISSUE_CODES = {
    "payout_wallet_currency_mismatch",
    "ledger_wallet_currency_mismatch",
    "ledger_payout_currency_mismatch",
    "negative_available_balance",
    "negative_locked_balance",
    "negative_ledger_amount",
    "orphan_payout_ledger_entry",
    "ledger_payout_wallet_mismatch",
    "duplicate_payout_reserve_ledger",
    "payout_reserve_amount_mismatch",
    "paid_payout_missing_payout_ledger",
}


class PayoutRepairExecutionService:
    """Execute only deterministic payout repairs derived from integrity issues.

    v73 intentionally keeps this outside PayoutService because reconciliation preview and
    execution are ops workflows, not normal payout lifecycle transitions.
    """

    @staticmethod
    def _money(value: Any) -> Decimal:
        try:
            return Decimal(str(value or "0.00"))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0.00")

    @staticmethod
    def _money_text(value: Decimal) -> str:
        return f"{value.quantize(Decimal('0.01'))}"

    @classmethod
    def _manual_result(cls, issue: dict[str, Any], *, reason: str | None = None) -> dict[str, Any]:
        return {
            "issue_code": issue.get("code", "unknown"),
            "action_code": "manual_review_required",
            "status": "manual_review_required",
            "reason": reason or "Issue is not eligible for automatic repair.",
            "payout_id": str(issue.get("payout_id") or ""),
            "wallet_id": str(issue.get("wallet_id") or ""),
            "trainer_id": str(issue.get("trainer_id") or ""),
            "currency": str(issue.get("currency") or issue.get("payout_currency") or issue.get("wallet_currency") or ""),
        }

    @classmethod
    def _repair_locked_balance_mismatch(cls, issue: dict[str, Any]) -> dict[str, Any]:
        wallet_id = issue.get("wallet_id")
        if not wallet_id:
            return cls._manual_result(issue, reason="Integrity issue has no wallet_id.")

        delta = cls._money(issue.get("delta"))
        if delta == Decimal("0.00"):
            return {**cls._manual_result(issue, reason="No balance delta to repair."), "status": "skipped"}

        wallet = TrainerWallet.objects.select_for_update().select_related("trainer").get(id=wallet_id)
        amount = abs(delta)

        if wallet.currency != (issue.get("currency") or wallet.currency):
            return cls._manual_result(issue, reason="Currency mismatch requires manual review.")

        if delta > Decimal("0.00"):
            # locked_amount is higher than active payout sum: release excess to available.
            if wallet.locked_amount < amount:
                return cls._manual_result(issue, reason="Locked balance is lower than requested release amount.")
            before = {"available_amount": wallet.available_amount, "locked_amount": wallet.locked_amount}
            wallet.locked_amount -= amount
            wallet.available_amount += amount
            wallet.save(update_fields=["available_amount", "locked_amount", "updated_at"])
            entry = BalanceEntry.objects.create(
                wallet=wallet,
                entry_type=BalanceEntry.EntryType.ADJUSTMENT,
                direction="credit",
                amount=amount,
                currency=wallet.currency,
                status="available",
                source_type="payout_repair_execution",
                source_id=wallet.id,
            )
            return {
                "issue_code": "locked_balance_mismatch",
                "action_code": "release_excess_locked_to_available",
                "status": "repaired",
                "wallet_id": str(wallet.id),
                "trainer_id": str(wallet.trainer.user_id),
                "currency": wallet.currency,
                "amount": cls._money_text(amount),
                "ledger_entry_id": str(entry.id),
                "before": {key: cls._money_text(value) for key, value in before.items()},
                "after": {
                    "available_amount": cls._money_text(wallet.available_amount),
                    "locked_amount": cls._money_text(wallet.locked_amount),
                },
            }

        # delta < 0: active payout sum is higher than locked balance.
        if wallet.available_amount < amount:
            return cls._manual_result(issue, reason="Insufficient available balance to move into locked balance.")

        before = {"available_amount": wallet.available_amount, "locked_amount": wallet.locked_amount}
        wallet.available_amount -= amount
        wallet.locked_amount += amount
        wallet.save(update_fields=["available_amount", "locked_amount", "updated_at"])
        entry = BalanceEntry.objects.create(
            wallet=wallet,
            entry_type=BalanceEntry.EntryType.ADJUSTMENT,
            direction="debit",
            amount=amount,
            currency=wallet.currency,
            status="locked",
            source_type="payout_repair_execution",
            source_id=wallet.id,
        )
        return {
            "issue_code": "locked_balance_mismatch",
            "action_code": "move_available_to_locked",
            "status": "repaired",
            "wallet_id": str(wallet.id),
            "trainer_id": str(wallet.trainer.user_id),
            "currency": wallet.currency,
            "amount": cls._money_text(amount),
            "ledger_entry_id": str(entry.id),
            "before": {key: cls._money_text(value) for key, value in before.items()},
            "after": {
                "available_amount": cls._money_text(wallet.available_amount),
                "locked_amount": cls._money_text(wallet.locked_amount),
            },
        }

    @classmethod
    def _repair_missing_reserve_entry(cls, issue: dict[str, Any]) -> dict[str, Any]:
        payout_id = issue.get("payout_id")
        if not payout_id:
            return cls._manual_result(issue, reason="Integrity issue has no payout_id.")

        payout = PayoutRequest.objects.select_for_update().select_related("wallet", "trainer").get(id=payout_id)
        if payout.status not in ACTIVE_PAYOUT_STATUSES:
            return cls._manual_result(issue, reason="Reserve ledger can only be auto-created for active payout states.")
        if payout.currency != payout.wallet.currency:
            return cls._manual_result(issue, reason="Currency mismatch requires manual review.")

        existing = BalanceEntry.objects.filter(
            wallet=payout.wallet,
            source_type="payout_request",
            source_id=payout.id,
            entry_type=BalanceEntry.EntryType.RESERVE,
        ).first()
        if existing:
            return {
                "issue_code": "active_payout_missing_reserve_ledger",
                "action_code": "create_missing_reserve_ledger",
                "status": "skipped",
                "reason": "Reserve ledger entry already exists.",
                "payout_id": str(payout.id),
                "wallet_id": str(payout.wallet_id),
                "ledger_entry_id": str(existing.id),
            }

        entry = BalanceEntry.objects.create(
            wallet=payout.wallet,
            entry_type=BalanceEntry.EntryType.RESERVE,
            direction="debit",
            amount=payout.amount,
            currency=payout.currency,
            status="locked",
            source_type="payout_request",
            source_id=payout.id,
        )
        return {
            "issue_code": "active_payout_missing_reserve_ledger",
            "action_code": "create_missing_reserve_ledger",
            "status": "repaired",
            "payout_id": str(payout.id),
            "wallet_id": str(payout.wallet_id),
            "trainer_id": str(payout.trainer.user_id),
            "currency": payout.currency,
            "amount": cls._money_text(payout.amount),
            "ledger_entry_id": str(entry.id),
        }

    @classmethod
    def _repair_missing_release_entry(cls, issue: dict[str, Any]) -> dict[str, Any]:
        payout_id = issue.get("payout_id")
        if not payout_id:
            return cls._manual_result(issue, reason="Integrity issue has no payout_id.")

        payout = PayoutRequest.objects.select_for_update().select_related("wallet", "trainer").get(id=payout_id)
        if payout.status != PayoutRequest.Status.REJECTED:
            return cls._manual_result(issue, reason="Release ledger can only be auto-created for rejected payouts.")
        if payout.currency != payout.wallet.currency:
            return cls._manual_result(issue, reason="Currency mismatch requires manual review.")

        existing = BalanceEntry.objects.filter(
            wallet=payout.wallet,
            source_type="payout_request",
            source_id=payout.id,
            entry_type=BalanceEntry.EntryType.RELEASE,
        ).first()
        if existing:
            return {
                "issue_code": "rejected_payout_missing_release_ledger",
                "action_code": "create_missing_release_ledger",
                "status": "skipped",
                "reason": "Release ledger entry already exists.",
                "payout_id": str(payout.id),
                "wallet_id": str(payout.wallet_id),
                "ledger_entry_id": str(existing.id),
            }

        entry = BalanceEntry.objects.create(
            wallet=payout.wallet,
            entry_type=BalanceEntry.EntryType.RELEASE,
            direction="credit",
            amount=payout.amount,
            currency=payout.currency,
            status="released",
            source_type="payout_request",
            source_id=payout.id,
        )
        return {
            "issue_code": "rejected_payout_missing_release_ledger",
            "action_code": "create_missing_release_ledger",
            "status": "repaired",
            "payout_id": str(payout.id),
            "wallet_id": str(payout.wallet_id),
            "trainer_id": str(payout.trainer.user_id),
            "currency": payout.currency,
            "amount": cls._money_text(payout.amount),
            "ledger_entry_id": str(entry.id),
        }

    @classmethod
    def _execute_issue(cls, issue: dict[str, Any]) -> dict[str, Any]:
        code = str(issue.get("code") or "")
        if code in MANUAL_REVIEW_ISSUE_CODES or code not in SAFE_AUTO_REPAIR_ISSUE_CODES:
            return cls._manual_result(issue)
        if code == "locked_balance_mismatch":
            return cls._repair_locked_balance_mismatch(issue)
        if code == "active_payout_missing_reserve_ledger":
            return cls._repair_missing_reserve_entry(issue)
        if code == "rejected_payout_missing_release_ledger":
            return cls._repair_missing_release_entry(issue)
        return cls._manual_result(issue)

    @classmethod
    @transaction.atomic
    def execute(cls, *, params: dict[str, Any] | None = None, actor=None, request=None) -> dict[str, Any]:
        params = dict(params or {})
        batch_size = min(max(int(params.get("batch_size") or params.get("limit") or 25), 1), 100)
        snapshot_params = {
            "status": str(params.get("status") or ""),
            "trainer_id": str(params.get("trainer_id") or ""),
            "currency": str(params.get("currency") or ""),
            "created_from": str(params.get("created_from") or ""),
            "created_to": str(params.get("created_to") or ""),
            "limit": max(batch_size, 100),
        }
        before = build_payout_integrity_snapshot(snapshot_params)
        issues = list(before.get("issues") or [])[:batch_size]
        results = [cls._execute_issue(issue) for issue in issues]
        repaired_count = sum(1 for item in results if item.get("status") == "repaired")
        skipped_count = sum(1 for item in results if item.get("status") == "skipped")
        manual_review_count = sum(1 for item in results if item.get("status") == "manual_review_required")
        after = build_payout_integrity_snapshot(snapshot_params)
        preview_after = build_payout_repair_preview({**snapshot_params, "batch_size": batch_size})

        AuditService.log_admin_action(
            actor=actor,
            request=request,
            action="payouts.repair_execution",
            target_type="payout_repair_execution",
            target_id="v73",
            status="completed",
            context={
                "filters": snapshot_params,
                "batch_size": batch_size,
                "repaired_count": repaired_count,
                "skipped_count": skipped_count,
                "manual_review_count": manual_review_count,
                "results": results,
            },
        )

        return {
            "generated_at": timezone.now(),
            "mode": "repair_execution",
            "repair_performed": repaired_count > 0,
            "filters": {**snapshot_params, "batch_size": batch_size},
            "summary": {
                "before_issue_count": before.get("summary", {}).get("issue_count", 0),
                "after_issue_count": after.get("summary", {}).get("issue_count", 0),
                "processed_count": len(results),
                "repaired_count": repaired_count,
                "skipped_count": skipped_count,
                "manual_review_count": manual_review_count,
                "has_more_before": len(before.get("issues") or []) > batch_size,
                "after_status": after.get("summary", {}).get("status", "unknown"),
            },
            "results": results,
            "manual_review_required_codes": sorted(MANUAL_REVIEW_ISSUE_CODES),
            "safe_auto_repair_codes": sorted(SAFE_AUTO_REPAIR_ISSUE_CODES),
            "integrity_before": {
                "issue_codes": before.get("issue_codes", {}),
                "issue_severities": before.get("issue_severities", {}),
            },
            "integrity_after": {
                "issue_codes": after.get("issue_codes", {}),
                "issue_severities": after.get("issue_severities", {}),
            },
            "repair_preview_after": preview_after,
        }
