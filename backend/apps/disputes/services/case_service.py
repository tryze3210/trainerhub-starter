from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.disputes.models import DisputeCase, DisputeEvent, RefundReview, ChargebackOperation, SupportInboxItem
from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus
from apps.payments.models import Payment
from apps.payments.services import PaymentService


@dataclass
class CreateDisputeCaseDTO:
    opened_by_id: int
    dispute_type: str
    subject: str
    summary: str = ""
    reason_code: str = ""
    trainer_id: str | None = None
    order_id: str | None = None
    payment_id: str | None = None


class DisputeCaseService:
    @staticmethod
    def _generate_public_id() -> str:
        return timezone.now().strftime("DSP%Y%m%d%H%M%S%f")

    @classmethod
    def create_case(cls, dto: CreateDisputeCaseDTO) -> DisputeCase:
        case = DisputeCase.objects.create(
            public_id=cls._generate_public_id(),
            opened_by_id=dto.opened_by_id,
            dispute_type=dto.dispute_type,
            subject=dto.subject,
            summary=dto.summary,
            reason_code=dto.reason_code,
            trainer_id=dto.trainer_id,
            order_id=dto.order_id,
            payment_id=dto.payment_id,
        )
        DisputeEvent.objects.create(dispute_case=case, actor_id=dto.opened_by_id, event_type=DisputeEvent.EVENT_CREATED, body=dto.summary)
        if dto.dispute_type == DisputeCase.TYPE_REFUND:
            RefundReview.objects.create(dispute_case=case)
        if dto.dispute_type == DisputeCase.TYPE_CHARGEBACK:
            ChargebackOperation.objects.create(dispute_case=case)
        SupportInboxItem.objects.create(dispute_case=case)
        return case

    @staticmethod
    def set_status(case: DisputeCase, *, actor_id: int | None, status: str, note: str = "") -> DisputeCase:
        case.status = status
        if status in {DisputeCase.STATUS_RESOLVED, DisputeCase.STATUS_REJECTED}:
            case.resolved_at = timezone.now()
        case.save(update_fields=["status", "resolved_at", "updated_at"])
        DisputeEvent.objects.create(
            dispute_case=case,
            actor_id=actor_id,
            event_type=DisputeEvent.EVENT_STATUS_CHANGED,
            body=note,
            payload={"status": status},
        )
        return case


class ChargebackDisputeService:
    @staticmethod
    def _operation_payload(operation: ChargebackOperation) -> dict[str, Any]:
        case = operation.dispute_case
        return {
            "id": str(operation.id),
            "case_id": str(case.id),
            "public_id": case.public_id,
            "payment_id": str(case.payment_id or ""),
            "order_id": str(case.order_id or ""),
            "provider_case_id": operation.provider_case_id,
            "network": operation.network,
            "amount": str(operation.amount),
            "currency": operation.currency,
            "status": operation.status,
            "evidence_due_at": operation.evidence_due_at.isoformat() if operation.evidence_due_at else None,
            "evidence_payload": operation.evidence_payload or {},
            "provider_payload": operation.provider_payload or {},
            "case_status": case.status,
        }

    @staticmethod
    def _money(value, fallback) -> Decimal:
        return Decimal(str(value if value is not None else fallback)).quantize(Decimal("0.01"))

    @staticmethod
    def _active_order_entitlements(payment: Payment):
        return Entitlement.objects.select_for_update().filter(
            source_type=EntitlementSourceType.ORDER,
            source_order=payment.order,
            status=EntitlementStatus.ACTIVE,
        )

    @classmethod
    def _hold_entitlements(
        cls,
        *,
        payment: Payment,
        case: DisputeCase,
        operation: ChargebackOperation,
        reason: str,
    ) -> int:
        held_at = timezone.now().isoformat()
        updated = 0
        for entitlement in cls._active_order_entitlements(payment):
            metadata = dict(entitlement.metadata or {})
            if metadata.get("access_hold") and metadata.get("chargeback_operation_id") == str(operation.id):
                continue
            metadata.update(
                {
                    "access_hold": True,
                    "access_hold_reason": reason,
                    "access_hold_started_at": metadata.get("access_hold_started_at") or held_at,
                    "chargeback_case_id": str(case.id),
                    "chargeback_operation_id": str(operation.id),
                    "provider_case_id": operation.provider_case_id,
                }
            )
            entitlement.metadata = metadata
            entitlement.save(update_fields=["metadata", "updated_at"])
            updated += 1
        return updated

    @classmethod
    def _release_entitlement_holds(
        cls,
        *,
        payment: Payment,
        operation: ChargebackOperation,
    ) -> int:
        released_at = timezone.now().isoformat()
        updated = 0
        for entitlement in cls._active_order_entitlements(payment):
            metadata = dict(entitlement.metadata or {})
            if metadata.get("chargeback_operation_id") != str(operation.id):
                continue
            for key in (
                "access_hold",
                "access_hold_reason",
                "access_hold_started_at",
                "chargeback_case_id",
                "chargeback_operation_id",
                "provider_case_id",
            ):
                metadata.pop(key, None)
            metadata["access_hold_released_at"] = released_at
            metadata["access_hold_release_reason"] = "chargeback_won"
            entitlement.metadata = metadata
            entitlement.save(update_fields=["metadata", "updated_at"])
            updated += 1
        return updated

    @classmethod
    def open_chargeback(
        cls,
        *,
        operator,
        payment_id: str,
        provider_case_id: str = "",
        network: str = "",
        amount=None,
        currency: str = "",
        evidence_due_at=None,
        provider_payload: dict[str, Any] | None = None,
        reason: str = "",
        request=None,
    ) -> dict[str, Any]:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related("order", "order__user").get(id=payment_id)
            case = (
                DisputeCase.objects.select_for_update()
                .filter(dispute_type=DisputeCase.TYPE_CHARGEBACK, payment_id=payment.id)
                .order_by("-created_at")
                .first()
            )
            if case is None:
                case = DisputeCaseService.create_case(
                    CreateDisputeCaseDTO(
                        opened_by_id=operator.id,
                        dispute_type=DisputeCase.TYPE_CHARGEBACK,
                        subject=f"Chargeback for payment {payment.id}",
                        summary=reason,
                        reason_code="chargeback_opened",
                        order_id=str(payment.order_id),
                        payment_id=str(payment.id),
                    )
                )

            operation, _created = ChargebackOperation.objects.select_for_update().get_or_create(dispute_case=case)
            operation.provider_case_id = provider_case_id or operation.provider_case_id
            operation.network = network or operation.network
            operation.amount = cls._money(amount, payment.amount)
            operation.currency = currency or payment.currency
            operation.status = ChargebackOperation.STATUS_OPEN
            operation.evidence_due_at = evidence_due_at or operation.evidence_due_at
            operation.provider_payload = {**(operation.provider_payload or {}), **(provider_payload or {})}
            operation.save(
                update_fields=[
                    "provider_case_id",
                    "network",
                    "amount",
                    "currency",
                    "status",
                    "evidence_due_at",
                    "provider_payload",
                    "updated_at",
                ]
            )

            PaymentService.mark_disputed(
                payment=payment,
                provider_payload={
                    "chargeback_case_id": str(case.id),
                    "chargeback_operation_id": str(operation.id),
                    "provider_case_id": operation.provider_case_id,
                    **(provider_payload or {}),
                },
                request=request,
            )
            payment.refresh_from_db()
            held_count = cls._hold_entitlements(
                payment=payment,
                case=case,
                operation=operation,
                reason="chargeback_opened",
            )
            DisputeEvent.objects.create(
                dispute_case=case,
                actor=operator,
                event_type=DisputeEvent.EVENT_CHARGEBACK_SYNCED,
                body=reason,
                payload={
                    "action": "opened",
                    "payment_id": str(payment.id),
                    "operation_id": str(operation.id),
                    "provider_case_id": operation.provider_case_id,
                    "held_entitlements_count": held_count,
                },
            )
            AuditService.log_admin_action(
                action="chargeback.opened",
                target_type="chargeback_operation",
                target_id=str(operation.id),
                actor=operator,
                request=request,
                reason=reason,
                context={
                    "case_id": str(case.id),
                    "payment_id": str(payment.id),
                    "order_id": str(payment.order_id),
                    "held_entitlements_count": held_count,
                },
            )
            return {**cls._operation_payload(operation), "held_entitlements_count": held_count}

    @classmethod
    def submit_evidence(
        cls,
        *,
        operator,
        operation: ChargebackOperation,
        evidence_payload: dict[str, Any],
        note: str = "",
        request=None,
    ) -> dict[str, Any]:
        with transaction.atomic():
            operation = ChargebackOperation.objects.select_for_update().select_related("dispute_case").get(pk=operation.pk)
            operation.evidence_payload = {
                **(operation.evidence_payload or {}),
                **(evidence_payload or {}),
                "submitted_at": timezone.now().isoformat(),
                "submitted_by_id": str(operator.id),
            }
            operation.status = ChargebackOperation.STATUS_OPEN
            operation.save(update_fields=["evidence_payload", "status", "updated_at"])
            DisputeEvent.objects.create(
                dispute_case=operation.dispute_case,
                actor=operator,
                event_type=DisputeEvent.EVENT_CHARGEBACK_SYNCED,
                body=note,
                payload={"action": "evidence_submitted", "operation_id": str(operation.id), "evidence": operation.evidence_payload},
            )
            AuditService.log_admin_action(
                action="chargeback.evidence_submitted",
                target_type="chargeback_operation",
                target_id=str(operation.id),
                actor=operator,
                request=request,
                reason=note,
                context={"case_id": str(operation.dispute_case_id), "evidence_keys": sorted(operation.evidence_payload.keys())},
            )
            return cls._operation_payload(operation)

    @classmethod
    def resolve(
        cls,
        *,
        operator,
        operation: ChargebackOperation,
        outcome: str,
        provider_payload: dict[str, Any] | None = None,
        note: str = "",
        request=None,
    ) -> dict[str, Any]:
        if outcome not in {ChargebackOperation.STATUS_WON, ChargebackOperation.STATUS_LOST}:
            raise ValueError("outcome must be won or lost")
        with transaction.atomic():
            operation = ChargebackOperation.objects.select_for_update().select_related("dispute_case").get(pk=operation.pk)
            case = operation.dispute_case
            payment = Payment.objects.select_for_update().select_related("order", "order__user").get(id=case.payment_id)
            payload = {
                "chargeback_case_id": str(case.id),
                "chargeback_operation_id": str(operation.id),
                "provider_case_id": operation.provider_case_id,
                **(provider_payload or {}),
            }
            if outcome == ChargebackOperation.STATUS_WON:
                payment = PaymentService.mark_chargeback_won(payment=payment, provider_payload=payload, request=request)
                released_count = cls._release_entitlement_holds(payment=payment, operation=operation)
                case_status = DisputeCase.STATUS_RESOLVED
            else:
                payment = PaymentService.mark_chargeback_lost(payment=payment, provider_payload=payload, request=request)
                released_count = 0
                case_status = DisputeCase.STATUS_REJECTED

            operation.status = outcome
            operation.provider_payload = {**(operation.provider_payload or {}), **(provider_payload or {})}
            operation.save(update_fields=["status", "provider_payload", "updated_at"])
            case.status = case_status
            case.resolution_note = note
            case.resolved_at = timezone.now()
            case.save(update_fields=["status", "resolution_note", "resolved_at", "updated_at"])
            DisputeEvent.objects.create(
                dispute_case=case,
                actor=operator,
                event_type=DisputeEvent.EVENT_CHARGEBACK_SYNCED,
                body=note,
                payload={
                    "action": f"resolved_{outcome}",
                    "operation_id": str(operation.id),
                    "payment_id": str(payment.id),
                    "payment_status": payment.status,
                    "released_entitlements_count": released_count,
                },
            )
            AuditService.log_admin_action(
                action=f"chargeback.{outcome}",
                target_type="chargeback_operation",
                target_id=str(operation.id),
                actor=operator,
                request=request,
                reason=note,
                context={
                    "case_id": str(case.id),
                    "payment_id": str(payment.id),
                    "payment_status": payment.status,
                    "released_entitlements_count": released_count,
                },
            )
            return {**cls._operation_payload(operation), "released_entitlements_count": released_count}
