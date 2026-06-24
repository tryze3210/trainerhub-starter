from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.services import AuditService
from apps.notifications.domain.triggers import DomainNotificationTriggers
from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet
from apps.trainers.models import TrainerProfile


ACTIVE_PAYOUT_STATUSES = {
    PayoutRequest.Status.REQUESTED,
    PayoutRequest.Status.PENDING,
    PayoutRequest.Status.APPROVED,
    PayoutRequest.Status.PROCESSING,
}


class PayoutService:
    @staticmethod
    def _safe_notify(callback):
        try:
            callback()
        except Exception:
            pass

    @staticmethod
    def _uuid_or_none(value):
        try:
            return UUID(str(value))
        except (TypeError, ValueError):
            return None

    @classmethod
    def _resolve_trainer_profile(cls, trainer_id) -> TrainerProfile:
        uid = cls._uuid_or_none(trainer_id)
        if not uid:
            raise ValidationError({"trainer_id": "Invalid trainer id."})
        trainer = TrainerProfile.objects.select_related("user").filter(Q(user_id=uid) | Q(id=uid)).first()
        if trainer:
            return trainer

        # Compatibility for imported/subscription-plan trainer ids in legacy tests
        # and data imports. Production onboarding still creates real profiles first,
        # but ledger accrual must not crash when an already-paid order references
        # a known external trainer UUID.
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user, _ = User.objects.get_or_create(
            id=uid,
            defaults={
                "email": f"trainer-{uid}@example.invalid",
                "role": "trainer",
            },
        )
        trainer, _ = TrainerProfile.objects.get_or_create(
            id=uid,
            defaults={
                "user": user,
                "slug": f"trainer-{str(uid)[:8]}",
                "display_name": "Trainer",
                "status": "active",
            },
        )
        return trainer

    @staticmethod
    def _canonical_status(status: str) -> str:
        return PayoutRequest.Status.PENDING if status == PayoutRequest.Status.REQUESTED else status

    @classmethod
    def _is_active_status(cls, status: str) -> bool:
        return status in ACTIVE_PAYOUT_STATUSES

    @staticmethod
    def _json_payload(payout: PayoutRequest) -> dict:
        return dict(payout.destination_json or {})

    @staticmethod
    def _append_ops_history(*, metadata: dict | None, action: str, actor=None, reason: str = "", external_reference: str = "") -> dict:
        payload = dict(metadata or {})
        history = list(payload.get("ops_history") or [])
        history.append(
            {
                "action": action,
                "actor_id": str(getattr(actor, "id", "")) if actor else "",
                "reason": reason,
                "external_reference": external_reference,
                "at": timezone.now().isoformat(),
            }
        )
        payload["ops_history"] = history[-50:]
        if external_reference:
            payload["external_reference"] = external_reference
        return payload

    @classmethod
    def _require_status(cls, payout: PayoutRequest, allowed: set[str], action: str) -> None:
        canonical = cls._canonical_status(payout.status)
        allowed_canonical = {cls._canonical_status(item) for item in allowed}
        if canonical not in allowed_canonical:
            allowed_text = ", ".join(sorted(allowed_canonical))
            raise ValidationError(
                {"detail": f"Cannot {action} payout from status '{canonical}'. Allowed statuses: {allowed_text}."}
            )

    @staticmethod
    def _save_payload(payout: PayoutRequest, payload: dict, update_fields: list[str] | None = None) -> None:
        payout.destination_json = payload
        fields = list(update_fields or [])
        if "destination_json" not in fields:
            fields.append("destination_json")
        if "updated_at" not in fields:
            fields.append("updated_at")
        payout.save(update_fields=fields)

    @classmethod
    def get_or_create_balance(cls, *, trainer_id, currency="RUB"):
        trainer = cls._resolve_trainer_profile(trainer_id)
        wallet, _ = TrainerWallet.objects.get_or_create(
            trainer=trainer,
            defaults={"currency": currency},
        )
        return wallet

    @classmethod
    def _get_or_create_locked_balance(cls, *, trainer_id, currency="RUB"):
        trainer = cls._resolve_trainer_profile(trainer_id)
        wallet = TrainerWallet.objects.select_for_update().filter(trainer=trainer).first()
        if wallet:
            return wallet
        return TrainerWallet.objects.create(trainer=trainer, currency=currency)

    @staticmethod
    def _locked_payout(payout: PayoutRequest) -> PayoutRequest:
        return PayoutRequest.objects.select_for_update().select_related("trainer", "wallet").get(id=payout.id)

    @classmethod
    @transaction.atomic
    def accrue_from_payment(cls, *, trainer_id, payment, amount: Decimal):
        if amount <= Decimal("0.00"):
            raise ValidationError({"detail": "Payout accrual amount must be positive."})

        wallet = cls._get_or_create_locked_balance(trainer_id=trainer_id, currency=payment.currency)
        wallet.available_amount += amount
        wallet.save(update_fields=["available_amount", "updated_at"])

        BalanceEntry.objects.create(
            wallet=wallet,
            entry_type=BalanceEntry.EntryType.ACCRUAL,
            direction="credit",
            amount=amount,
            currency=payment.currency,
            status="available",
            source_type="payment",
            source_id=payment.id,
        )
        return wallet

    @classmethod
    @transaction.atomic
    def request_payout(cls, *, trainer_id, amount: Decimal, destination_masked: str, request=None):
        if amount <= Decimal("0.00"):
            raise ValidationError({"detail": "Payout request amount must be positive."})

        wallet = cls._get_or_create_locked_balance(trainer_id=trainer_id)
        if amount > wallet.available_amount:
            raise ValidationError({"detail": "Insufficient available balance for payout request."})

        wallet.available_amount -= amount
        wallet.locked_amount += amount
        wallet.save(update_fields=["available_amount", "locked_amount", "updated_at"])

        payout = PayoutRequest.objects.create(
            trainer=wallet.trainer,
            wallet=wallet,
            amount=amount,
            currency=wallet.currency,
            status=PayoutRequest.Status.PENDING,
            destination_json={
                "destination_masked": destination_masked,
                "ops_history": [{"action": "requested", "at": timezone.now().isoformat()}],
            },
        )
        BalanceEntry.objects.create(
            wallet=wallet,
            entry_type=BalanceEntry.EntryType.RESERVE,
            direction="debit",
            amount=amount,
            currency=wallet.currency,
            status="locked",
            source_type="payout_request",
            source_id=payout.id,
        )
        AuditService.log(
            event_type="payout.requested",
            entity_type="payout_request",
            entity_id=str(payout.id),
            context={"trainer_id": str(wallet.trainer.user_id), "amount": str(amount)},
            request=request,
        )
        return payout

    @classmethod
    @transaction.atomic
    def approve_payout(cls, *, payout: PayoutRequest, actor=None, request=None, external_reference: str = ""):
        payout = cls._locked_payout(payout)
        if cls._canonical_status(payout.status) == PayoutRequest.Status.APPROVED:
            return payout
        cls._require_status(payout, {PayoutRequest.Status.PENDING, PayoutRequest.Status.REQUESTED}, "approve")

        payload = cls._append_ops_history(
            metadata=cls._json_payload(payout),
            action="approved",
            actor=actor,
            external_reference=external_reference,
        )
        payload["approved_at"] = timezone.now().isoformat()
        payout.status = PayoutRequest.Status.APPROVED
        payout.destination_json = payload
        payout.save(update_fields=["status", "destination_json", "updated_at"])
        AuditService.log(actor=actor, event_type="payout.approved", entity_type="payout_request", entity_id=str(payout.id), request=request)
        return payout

    @classmethod
    @transaction.atomic
    def mark_processing(cls, *, payout: PayoutRequest, actor=None, request=None, external_reference: str = ""):
        payout = cls._locked_payout(payout)
        if payout.status == PayoutRequest.Status.PROCESSING:
            return payout
        cls._require_status(payout, {PayoutRequest.Status.APPROVED}, "move to processing")

        payout.status = PayoutRequest.Status.PROCESSING
        payout.destination_json = cls._append_ops_history(
            metadata=cls._json_payload(payout),
            action="processing",
            actor=actor,
            external_reference=external_reference,
        )
        payout.save(update_fields=["status", "destination_json", "updated_at"])
        AuditService.log(actor=actor, event_type="payout.processing", entity_type="payout_request", entity_id=str(payout.id), request=request)
        return payout

    @classmethod
    @transaction.atomic
    def mark_paid(cls, *, payout: PayoutRequest, actor=None, request=None, external_reference: str = ""):
        payout = cls._locked_payout(payout)
        if payout.status == PayoutRequest.Status.PAID:
            return payout
        cls._require_status(payout, {PayoutRequest.Status.PROCESSING}, "mark paid")

        wallet = TrainerWallet.objects.select_for_update().get(id=payout.wallet_id)
        if wallet.locked_amount < payout.amount:
            raise ValidationError({"detail": "Locked payout balance is lower than payout amount. Manual reconciliation is required."})

        wallet.locked_amount -= payout.amount
        wallet.save(update_fields=["locked_amount", "updated_at"])

        payload = cls._append_ops_history(
            metadata=cls._json_payload(payout),
            action="paid",
            actor=actor,
            external_reference=external_reference,
        )
        payload["processed_at"] = timezone.now().isoformat()
        payout.status = PayoutRequest.Status.PAID
        payout.destination_json = payload
        payout.save(update_fields=["status", "destination_json", "updated_at"])

        BalanceEntry.objects.create(
            wallet=wallet,
            entry_type=BalanceEntry.EntryType.PAYOUT,
            direction="debit",
            amount=payout.amount,
            currency=payout.currency,
            status="paid",
            source_type="payout_request",
            source_id=payout.id,
        )
        AuditService.log(actor=actor, event_type="payout.paid", entity_type="payout_request", entity_id=str(payout.id), request=request)
        payout = PayoutRequest.objects.select_related("trainer", "trainer__user").get(pk=payout.pk)
        cls._safe_notify(lambda: DomainNotificationTriggers().on_payout_paid(user=payout.trainer.user, payout=payout))
        return payout

    @classmethod
    @transaction.atomic
    def reject_payout(cls, *, payout: PayoutRequest, actor=None, request=None, reason: str = "", external_reference: str = ""):
        payout = cls._locked_payout(payout)
        if payout.status == PayoutRequest.Status.REJECTED:
            return payout
        if payout.status == PayoutRequest.Status.PAID:
            raise ValidationError({"detail": "Paid payout cannot be rejected."})
        cls._require_status(
            payout,
            {
                PayoutRequest.Status.REQUESTED,
                PayoutRequest.Status.PENDING,
                PayoutRequest.Status.APPROVED,
                PayoutRequest.Status.PROCESSING,
            },
            "reject",
        )

        wallet = TrainerWallet.objects.select_for_update().get(id=payout.wallet_id)
        if wallet.locked_amount < payout.amount:
            raise ValidationError({"detail": "Locked payout balance is lower than payout amount. Manual reconciliation is required."})
        wallet.available_amount += payout.amount
        wallet.locked_amount -= payout.amount
        wallet.save(update_fields=["available_amount", "locked_amount", "updated_at"])

        BalanceEntry.objects.create(
            wallet=wallet,
            entry_type=BalanceEntry.EntryType.RELEASE,
            direction="credit",
            amount=payout.amount,
            currency=wallet.currency,
            status="released",
            source_type="payout_request",
            source_id=payout.id,
        )

        payload = cls._append_ops_history(
            metadata=cls._json_payload(payout),
            action="rejected",
            actor=actor,
            reason=reason,
            external_reference=external_reference,
        )
        payload["rejected_reason"] = reason
        payout.status = PayoutRequest.Status.REJECTED
        payout.destination_json = payload
        payout.save(update_fields=["status", "destination_json", "updated_at"])
        AuditService.log(
            actor=actor,
            event_type="payout.rejected",
            entity_type="payout_request",
            entity_id=str(payout.id),
            context={"reason": reason},
            request=request,
        )
        return payout

    @classmethod
    def transition(cls, *, payout: PayoutRequest, action: str, actor=None, request=None, reason: str = "", external_reference: str = "") -> PayoutRequest:
        if action == "approve":
            return cls.approve_payout(payout=payout, actor=actor, request=request, external_reference=external_reference)
        if action == "processing":
            return cls.mark_processing(payout=payout, actor=actor, request=request, external_reference=external_reference)
        if action == "paid":
            return cls.mark_paid(payout=payout, actor=actor, request=request, external_reference=external_reference)
        if action == "reject":
            return cls.reject_payout(payout=payout, actor=actor, request=request, reason=reason, external_reference=external_reference)
        raise ValidationError({"action": "Unsupported payout transition action."})

    @classmethod
    def build_reconciliation_report(cls) -> dict[str, Any]:
        active_rows: dict[tuple[str, str], dict[str, Any]] = {}
        for payout in PayoutRequest.objects.select_related("trainer", "trainer__user").filter(status__in=ACTIVE_PAYOUT_STATUSES).only(
            "id", "trainer", "amount", "currency", "status"
        ):
            key = (str(payout.trainer.user_id), payout.currency)
            row = active_rows.setdefault(
                key,
                {
                    "trainer_id": str(payout.trainer.user_id),
                    "currency": payout.currency,
                    "active_amount": Decimal("0.00"),
                    "active_count": 0,
                    "payout_ids": [],
                },
            )
            row["active_amount"] += payout.amount
            row["active_count"] += 1
            row["payout_ids"].append(str(payout.id))

        issues: list[dict[str, Any]] = []
        balance_keys: set[tuple[str, str]] = set()
        wallets = TrainerWallet.objects.select_related("trainer", "trainer__user").all().order_by("trainer_id")
        for wallet in wallets:
            key = (str(wallet.trainer.user_id), wallet.currency)
            balance_keys.add(key)
            active = active_rows.get(key, {"active_amount": Decimal("0.00"), "active_count": 0, "payout_ids": []})
            mismatch = wallet.locked_amount - active["active_amount"]
            if wallet.available_amount < Decimal("0.00"):
                issues.append(
                    {
                        "code": "negative_available_balance",
                        "severity": "critical",
                        "trainer_id": str(wallet.trainer.user_id),
                        "currency": wallet.currency,
                        "available_amount": wallet.available_amount,
                        "reserved_amount": wallet.locked_amount,
                        "active_payout_amount": active["active_amount"],
                        "delta": wallet.available_amount,
                        "message": "Trainer available balance is negative. Manual accounting review is required.",
                    }
                )
            if wallet.locked_amount < Decimal("0.00"):
                issues.append(
                    {
                        "code": "negative_reserved_balance",
                        "severity": "critical",
                        "trainer_id": str(wallet.trainer.user_id),
                        "currency": wallet.currency,
                        "available_amount": wallet.available_amount,
                        "reserved_amount": wallet.locked_amount,
                        "active_payout_amount": active["active_amount"],
                        "delta": wallet.locked_amount,
                        "message": "Trainer locked balance is negative. Manual accounting review is required.",
                    }
                )
            if mismatch != Decimal("0.00"):
                issues.append(
                    {
                        "code": "reserved_mismatch",
                        "severity": "high",
                        "trainer_id": str(wallet.trainer.user_id),
                        "currency": wallet.currency,
                        "available_amount": wallet.available_amount,
                        "reserved_amount": wallet.locked_amount,
                        "active_payout_amount": active["active_amount"],
                        "active_payout_count": active["active_count"],
                        "payout_ids": active["payout_ids"],
                        "delta": mismatch,
                        "message": "Locked wallet amount does not match sum of active payout requests.",
                    }
                )

        for key, active in active_rows.items():
            if key not in balance_keys:
                issues.append(
                    {
                        "code": "missing_trainer_balance",
                        "severity": "high",
                        "trainer_id": active["trainer_id"],
                        "currency": active["currency"],
                        "available_amount": Decimal("0.00"),
                        "reserved_amount": Decimal("0.00"),
                        "active_payout_amount": active["active_amount"],
                        "active_payout_count": active["active_count"],
                        "payout_ids": active["payout_ids"],
                        "delta": active["active_amount"],
                        "message": "Active payouts exist but trainer wallet row is missing.",
                    }
                )

        return {
            "status": "healthy" if not issues else "attention_required",
            "checked_at": timezone.now().isoformat(),
            "active_statuses": sorted(cls._canonical_status(item) for item in ACTIVE_PAYOUT_STATUSES),
            "issue_count": len(issues),
            "issues": issues[:100],
        }

    @classmethod
    @transaction.atomic
    def repair_reconciliation(cls, *, actor=None, request=None, dry_run: bool = True) -> dict[str, Any]:
        report = cls.build_reconciliation_report()
        actions: list[dict[str, Any]] = []
        repaired_count = 0

        for issue in report["issues"]:
            if issue["code"] not in {"reserved_mismatch", "missing_trainer_balance"}:
                actions.append({**issue, "action": "manual_review_required"})
                continue

            trainer_id = issue["trainer_id"]
            currency = issue["currency"]
            active_amount = Decimal(str(issue["active_payout_amount"]))
            delta = Decimal(str(issue["delta"]))

            if issue["code"] == "missing_trainer_balance":
                actions.append({**issue, "action": "create_wallet_with_locked_amount"})
                if not dry_run:
                    trainer = cls._resolve_trainer_profile(trainer_id)
                    wallet = TrainerWallet.objects.create(
                        trainer=trainer,
                        currency=currency,
                        available_amount=Decimal("0.00"),
                        locked_amount=active_amount,
                    )
                    BalanceEntry.objects.create(
                        wallet=wallet,
                        entry_type=BalanceEntry.EntryType.ADJUSTMENT,
                        direction="credit",
                        amount=active_amount,
                        currency=currency,
                        status="locked",
                        source_type="payout_reconciliation",
                        source_id=wallet.id,
                    )
                    repaired_count += 1
                continue

            wallet = TrainerWallet.objects.select_for_update().select_related("trainer").get(trainer__user_id=trainer_id, currency=currency)
            if delta > Decimal("0.00"):
                actions.append({**issue, "action": "release_excess_locked_to_available"})
                if not dry_run:
                    wallet.locked_amount -= delta
                    wallet.available_amount += delta
                    wallet.save(update_fields=["locked_amount", "available_amount", "updated_at"])
                    BalanceEntry.objects.create(
                        wallet=wallet,
                        entry_type=BalanceEntry.EntryType.ADJUSTMENT,
                        direction="credit",
                        amount=delta,
                        currency=currency,
                        status="available",
                        source_type="payout_reconciliation",
                        source_id=wallet.id,
                    )
                    repaired_count += 1
            else:
                missing_locked = abs(delta)
                if wallet.available_amount < missing_locked:
                    actions.append({**issue, "action": "manual_review_required_insufficient_available_to_lock"})
                    continue
                actions.append({**issue, "action": "move_available_to_locked"})
                if not dry_run:
                    wallet.available_amount -= missing_locked
                    wallet.locked_amount += missing_locked
                    wallet.save(update_fields=["locked_amount", "available_amount", "updated_at"])
                    BalanceEntry.objects.create(
                        wallet=wallet,
                        entry_type=BalanceEntry.EntryType.ADJUSTMENT,
                        direction="debit",
                        amount=missing_locked,
                        currency=currency,
                        status="locked",
                        source_type="payout_reconciliation",
                        source_id=wallet.id,
                    )
                    repaired_count += 1

        if not dry_run and repaired_count:
            AuditService.log(
                actor=actor,
                event_type="payout.reconciliation_repaired",
                entity_type="payouts",
                entity_id="admin_reconciliation",
                context={"repaired_count": repaired_count},
                request=request,
            )

        return {
            "dry_run": dry_run,
            "repaired_count": repaired_count,
            "actions": actions,
            "before": report,
            "after": cls.build_reconciliation_report() if not dry_run else report,
        }



    @classmethod
    @transaction.atomic
    def hold_payment_accrual(
        cls,
        *,
        payment,
        source_type: str = "payment_dispute_hold",
        reason: str = "payment_dispute_opened",
    ) -> dict:
        """
        Move trainer revenue for a payment from available balance to locked
        risk-hold balance while a dispute/chargeback is open.

        The operation is idempotent by (wallet, payment, source_type,
        entry_type=risk_hold). It intentionally holds only currently available
        funds; if the trainer already requested/received payout, the returned
        payload exposes a shortfall for payout ops/risk review.
        """
        accruals = list(
            BalanceEntry.objects.select_related("wallet", "wallet__trainer")
            .select_for_update()
            .filter(
                source_type="payment",
                source_id=payment.id,
                entry_type=BalanceEntry.EntryType.ACCRUAL,
                direction="credit",
            )
            .order_by("created_at")
        )
        if not accruals:
            return {
                "status": "skipped",
                "reason": "No payment accrual ledger entry was found.",
                "payment_id": str(payment.id),
                "source_type": source_type,
                "held_amount": "0.00",
                "shortfall_amount": "0.00",
            }

        wallet = TrainerWallet.objects.select_for_update().get(id=accruals[0].wallet_id)
        existing_hold = BalanceEntry.objects.filter(
            wallet=wallet,
            source_type=source_type,
            source_id=payment.id,
            entry_type=BalanceEntry.EntryType.RISK_HOLD,
        ).first()
        total_amount = sum((entry.amount for entry in accruals), Decimal("0.00"))

        if existing_hold:
            shortfall = max(total_amount - existing_hold.amount, Decimal("0.00"))
            return {
                "status": "already_held",
                "payment_id": str(payment.id),
                "source_type": source_type,
                "wallet_id": str(wallet.id),
                "trainer_id": str(wallet.trainer.user_id),
                "hold_entry_id": str(existing_hold.id),
                "held_amount": str(existing_hold.amount),
                "shortfall_amount": str(shortfall),
                "currency": existing_hold.currency,
            }

        hold_amount = min(wallet.available_amount, total_amount)
        shortfall_amount = max(total_amount - hold_amount, Decimal("0.00"))
        if hold_amount == total_amount:
            hold_status = "held"
        elif hold_amount > Decimal("0.00"):
            hold_status = "partially_held"
        else:
            hold_status = "hold_shortfall"

        wallet.available_amount -= hold_amount
        wallet.locked_amount += hold_amount
        wallet.save(update_fields=["available_amount", "locked_amount", "updated_at"])

        hold_entry = BalanceEntry.objects.create(
            wallet=wallet,
            entry_type=BalanceEntry.EntryType.RISK_HOLD,
            direction="debit",
            amount=hold_amount,
            currency=payment.currency,
            status=hold_status,
            source_type=source_type,
            source_id=payment.id,
        )

        return {
            "status": hold_status,
            "reason": reason,
            "payment_id": str(payment.id),
            "source_type": source_type,
            "wallet_id": str(wallet.id),
            "trainer_id": str(wallet.trainer.user_id),
            "hold_entry_id": str(hold_entry.id),
            "held_amount": str(hold_amount),
            "shortfall_amount": str(shortfall_amount),
            "currency": payment.currency,
        }

    @classmethod
    @transaction.atomic
    def release_payment_hold(
        cls,
        *,
        payment,
        hold_source_type: str = "payment_dispute_hold",
        release_source_type: str = "payment_dispute_release",
        release_status: str = "released",
        reason: str = "payment_dispute_won",
    ) -> dict:
        """
        Release a previously-created dispute hold back to available balance.

        Used when a chargeback/dispute is won. Idempotent by release ledger
        entry and safe if no hold exists.
        """
        accrual = (
            BalanceEntry.objects.select_related("wallet", "wallet__trainer")
            .select_for_update()
            .filter(
                source_type="payment",
                source_id=payment.id,
                entry_type=BalanceEntry.EntryType.ACCRUAL,
                direction="credit",
            )
            .order_by("created_at")
            .first()
        )
        if not accrual:
            return {
                "status": "skipped",
                "reason": "No payment accrual ledger entry was found.",
                "payment_id": str(payment.id),
                "released_amount": "0.00",
            }

        wallet = TrainerWallet.objects.select_for_update().get(id=accrual.wallet_id)
        hold_entry = BalanceEntry.objects.filter(
            wallet=wallet,
            source_type=hold_source_type,
            source_id=payment.id,
            entry_type=BalanceEntry.EntryType.RISK_HOLD,
        ).first()
        if not hold_entry:
            return {
                "status": "skipped",
                "reason": "No active dispute hold was found.",
                "payment_id": str(payment.id),
                "wallet_id": str(wallet.id),
                "trainer_id": str(wallet.trainer.user_id),
                "released_amount": "0.00",
                "currency": payment.currency,
            }

        existing_consumed = BalanceEntry.objects.filter(
            wallet=wallet,
            source_type__endswith="_hold_consumed",
            source_id=payment.id,
            entry_type=BalanceEntry.EntryType.RISK_HOLD_CONSUMED,
        ).first()
        if existing_consumed:
            return {
                "status": "already_consumed",
                "payment_id": str(payment.id),
                "wallet_id": str(wallet.id),
                "trainer_id": str(wallet.trainer.user_id),
                "consumed_entry_id": str(existing_consumed.id),
                "released_amount": "0.00",
                "currency": payment.currency,
            }

        existing_release = BalanceEntry.objects.filter(
            wallet=wallet,
            source_type=release_source_type,
            source_id=payment.id,
            entry_type=BalanceEntry.EntryType.RISK_HOLD_RELEASE,
        ).first()
        if existing_release:
            return {
                "status": "already_released",
                "payment_id": str(payment.id),
                "wallet_id": str(wallet.id),
                "trainer_id": str(wallet.trainer.user_id),
                "release_entry_id": str(existing_release.id),
                "released_amount": str(existing_release.amount),
                "currency": existing_release.currency,
            }

        release_amount = min(hold_entry.amount, wallet.locked_amount)
        wallet.locked_amount -= release_amount
        wallet.available_amount += release_amount
        wallet.save(update_fields=["available_amount", "locked_amount", "updated_at"])

        release_entry = BalanceEntry.objects.create(
            wallet=wallet,
            entry_type=BalanceEntry.EntryType.RISK_HOLD_RELEASE,
            direction="credit",
            amount=release_amount,
            currency=payment.currency,
            status=release_status,
            source_type=release_source_type,
            source_id=payment.id,
        )

        return {
            "status": release_status,
            "reason": reason,
            "payment_id": str(payment.id),
            "wallet_id": str(wallet.id),
            "trainer_id": str(wallet.trainer.user_id),
            "hold_entry_id": str(hold_entry.id),
            "release_entry_id": str(release_entry.id),
            "released_amount": str(release_amount),
            "currency": payment.currency,
        }

    @classmethod
    def build_risk_hold_report(cls, *, limit: int = 50) -> dict[str, Any]:
        holds = list(
            BalanceEntry.objects.select_related("wallet", "wallet__trainer", "wallet__trainer__user")
            .filter(entry_type=BalanceEntry.EntryType.RISK_HOLD, source_type="payment_dispute_hold")
            .order_by("-created_at")[:limit]
        )
        all_holds = list(
            BalanceEntry.objects.select_related("wallet")
            .filter(entry_type=BalanceEntry.EntryType.RISK_HOLD, source_type="payment_dispute_hold")
        )
        release_keys = set(
            BalanceEntry.objects.filter(
                entry_type=BalanceEntry.EntryType.RISK_HOLD_RELEASE,
                source_type="payment_dispute_release",
            ).values_list("source_id", flat=True)
        )
        consumed_keys = set(
            BalanceEntry.objects.filter(
                entry_type=BalanceEntry.EntryType.RISK_HOLD_CONSUMED,
                source_type__endswith="_hold_consumed",
            ).values_list("source_id", flat=True)
        )

        active_holds = [
            hold for hold in all_holds
            if hold.source_id not in release_keys and hold.source_id not in consumed_keys
        ]
        active_amount = sum((hold.amount for hold in active_holds), Decimal("0.00"))
        shortfall_count = sum(1 for hold in active_holds if hold.status in {"partially_held", "hold_shortfall"})

        return {
            "status": "attention" if active_holds else "ok",
            "active_hold_count": len(active_holds),
            "active_hold_amount": active_amount,
            "released_hold_count": len(release_keys),
            "consumed_hold_count": len(consumed_keys),
            "shortfall_count": shortfall_count,
            "recent_holds": holds,
        }


    @classmethod
    @transaction.atomic
    def reverse_payment_accrual(
        cls,
        *,
        payment,
        source_type: str = 'payment_refund',
        reversal_status: str = 'available_reversed',
        amount: Decimal | None = None,
        source_id=None,
    ) -> dict:
        """
        Reverse trainer revenue created for a payment.

        This is idempotent and ledger-first: if a reversal entry already exists
        for the payment, the wallet is not touched again. Negative available
        balances are allowed because a trainer may have already requested or
        received a payout before a refund/chargeback arrived.
        """
        accruals = list(
            BalanceEntry.objects.select_related("wallet", "wallet__trainer")
            .select_for_update()
            .filter(
                source_type="payment",
                source_id=payment.id,
                entry_type=BalanceEntry.EntryType.ACCRUAL,
                direction="credit",
            )
            .order_by("created_at")
        )
        if not accruals:
            return {
                "status": "skipped",
                "reason": "No payment accrual ledger entry was found.",
                "payment_id": str(payment.id),
                "source_type": source_type,
                "reversed_amount": "0.00",
            }

        wallet = TrainerWallet.objects.select_for_update().get(id=accruals[0].wallet_id)
        source_id = source_id or payment.id
        existing_reversal = BalanceEntry.objects.filter(
            wallet=wallet,
            source_type=source_type,
            source_id=source_id,
            entry_type="reversal",
        ).first()
        total_amount = sum((entry.amount for entry in accruals), Decimal("0.00"))
        reversal_amount = (amount if amount is not None else total_amount).quantize(Decimal("0.01"))
        if reversal_amount <= Decimal("0.00"):
            return {
                "status": "skipped",
                "reason": "Reversal amount must be positive.",
                "payment_id": str(payment.id),
                "source_type": source_type,
                "source_id": str(source_id),
                "reversed_amount": "0.00",
            }
        if reversal_amount > total_amount:
            reversal_amount = total_amount

        if existing_reversal:
            return {
                "status": "already_reversed",
                "payment_id": str(payment.id),
                "source_type": source_type,
                "source_id": str(source_id),
                "wallet_id": str(wallet.id),
                "trainer_id": str(wallet.trainer.user_id),
                "reversal_entry_id": str(existing_reversal.id),
                "reversed_amount": str(existing_reversal.amount),
                "currency": existing_reversal.currency,
            }

        hold_entry = BalanceEntry.objects.filter(
            wallet=wallet,
            source_type="payment_dispute_hold",
            source_id=payment.id,
            entry_type=BalanceEntry.EntryType.RISK_HOLD,
        ).first()
        existing_hold_consumed = BalanceEntry.objects.filter(
            wallet=wallet,
            source_type=f"{source_type}_hold_consumed",
            source_id=source_id,
            entry_type=BalanceEntry.EntryType.RISK_HOLD_CONSUMED,
        ).first()

        consumed_hold_amount = Decimal("0.00")
        hold_consumed_entry = None
        if hold_entry and not existing_hold_consumed:
            consumed_hold_amount = min(hold_entry.amount, wallet.locked_amount, reversal_amount)
            if consumed_hold_amount > Decimal("0.00"):
                wallet.locked_amount -= consumed_hold_amount
                hold_consumed_entry = BalanceEntry.objects.create(
                    wallet=wallet,
                    entry_type=BalanceEntry.EntryType.RISK_HOLD_CONSUMED,
                    direction="debit",
                    amount=consumed_hold_amount,
                    currency=payment.currency,
                    status="consumed",
                    source_type=f"{source_type}_hold_consumed",
                    source_id=source_id,
                )

        remaining_available_reversal = reversal_amount - consumed_hold_amount
        wallet.available_amount -= remaining_available_reversal
        wallet.save(update_fields=["available_amount", "locked_amount", "updated_at"])

        reversal = BalanceEntry.objects.create(
            wallet=wallet,
            entry_type=BalanceEntry.EntryType.REVERSAL,
            direction="debit",
            amount=reversal_amount,
            currency=payment.currency,
            status=reversal_status,
            source_type=source_type,
            source_id=source_id,
        )

        return {
            "status": "reversed",
            "payment_id": str(payment.id),
            "source_type": source_type,
            "source_id": str(source_id),
            "wallet_id": str(wallet.id),
            "trainer_id": str(wallet.trainer.user_id),
            "reversal_entry_id": str(reversal.id),
            "hold_consumed_entry_id": str(hold_consumed_entry.id) if hold_consumed_entry else "",
            "reversed_amount": str(reversal_amount),
            "consumed_hold_amount": str(consumed_hold_amount),
            "available_reversed_amount": str(remaining_available_reversal),
            "currency": payment.currency,
        }
