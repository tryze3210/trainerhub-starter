from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.services import AuditService


class UnsupportedRepairAction(ValueError):
    pass


class RepairTargetNotFound(ObjectDoesNotExist):
    pass


@dataclass(frozen=True)
class RepairResult:
    action: str
    status: str
    entity_type: str
    entity_id: str
    message: str
    changed: bool
    result: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value.quantize(Decimal('0.01')))
    if isinstance(value, UUID):
        return str(value)
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return value


def _id(value: Any) -> str:
    return str(value or '')


def _first_validation_message(exc: Exception) -> str:
    detail = getattr(exc, 'detail', None)
    if detail is None:
        return str(exc)
    return str(detail)


class ReconciliationRepairService:
    """Audited, operator-triggered repair actions for reconciliation issues.

    This service is intentionally explicit. It does not infer dangerous fixes from
    a generic issue payload. Each action requires a concrete entity type/id and
    has a narrow implementation path so admin operations remain auditable and
    predictable.
    """

    ACTIONS = {
        'retry_outbox',
        'mark_outbox_dead',
        'reprocess_webhook',
        'grant_order_access',
        'revoke_entitlement',
        'project_payout_accrual',
        'reverse_payout_accrual',
    }

    def execute(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        reason: str = '',
        force: bool = False,
        request=None,
    ) -> dict[str, Any]:
        if action not in self.ACTIONS:
            raise UnsupportedRepairAction(f'Unsupported reconciliation repair action: {action}')
        if not reason:
            raise ValidationError({'reason': 'Reason is required for reconciliation repair actions.'})

        try:
            if action == 'retry_outbox':
                result = self._retry_outbox(entity_type=entity_type, entity_id=entity_id, reason=reason)
            elif action == 'mark_outbox_dead':
                result = self._mark_outbox_dead(entity_type=entity_type, entity_id=entity_id, reason=reason)
            elif action == 'reprocess_webhook':
                result = self._reprocess_webhook(entity_type=entity_type, entity_id=entity_id, force=force)
            elif action == 'grant_order_access':
                result = self._grant_order_access(entity_type=entity_type, entity_id=entity_id, force=force)
            elif action == 'revoke_entitlement':
                result = self._revoke_entitlement(entity_type=entity_type, entity_id=entity_id, reason=reason, force=force)
            elif action == 'project_payout_accrual':
                result = self._project_payout_accrual(entity_type=entity_type, entity_id=entity_id, force=force)
            elif action == 'reverse_payout_accrual':
                result = self._reverse_payout_accrual(entity_type=entity_type, entity_id=entity_id, reason=reason, force=force)
            else:  # pragma: no cover - protected by ACTIONS check
                raise UnsupportedRepairAction(f'Unsupported reconciliation repair action: {action}')
        except ValidationError:
            raise
        except ObjectDoesNotExist as exc:
            raise RepairTargetNotFound(str(exc) or f'{entity_type} {entity_id} was not found.')

        payload = result.to_dict()
        audit_event = AuditService.log_admin_action(
            request=request,
            action=f'reconciliation.{action}',
            target_type=entity_type,
            target_id=entity_id,
            reason=reason,
            status=payload['status'],
            context={
                'force': force,
                'repair_result': payload,
            },
        )
        payload['audit_event_id'] = str(audit_event.id)
        payload['audit_event_href'] = f'/admin/entities/audit_event/{audit_event.id}'
        payload['entity_href'] = f'/admin/entities/{entity_type}/{entity_id}'
        payload['reconciliation_href'] = '/admin/reconciliation'
        payload['audit'] = {
            'event_id': str(audit_event.id),
            'event_type': audit_event.event_type,
            'entity_type': audit_event.entity_type,
            'entity_id': audit_event.entity_id,
            'created_at': audit_event.created_at.isoformat() if getattr(audit_event, 'created_at', None) else None,
        }
        return payload

    def _retry_outbox(self, *, entity_type: str, entity_id: str, reason: str) -> RepairResult:
        if entity_type != 'outbox_message':
            raise ValidationError({'entity_type': 'retry_outbox requires entity_type=outbox_message.'})
        from apps.events.services import DomainEventService

        payload = DomainEventService().retry_outbox_message(message_id=entity_id, reset_attempts=True)
        return RepairResult(
            action='retry_outbox',
            status='accepted',
            entity_type=entity_type,
            entity_id=entity_id,
            message='Outbox message was returned to pending state.',
            changed=True,
            result={'outbox_status': payload.get('status'), 'attempts': payload.get('attempts'), 'reason': reason},
        )

    def _mark_outbox_dead(self, *, entity_type: str, entity_id: str, reason: str) -> RepairResult:
        if entity_type != 'outbox_message':
            raise ValidationError({'entity_type': 'mark_outbox_dead requires entity_type=outbox_message.'})
        from apps.events.services import DomainEventService

        payload = DomainEventService().mark_outbox_dead(message_id=entity_id, reason=reason)
        return RepairResult(
            action='mark_outbox_dead',
            status='accepted',
            entity_type=entity_type,
            entity_id=entity_id,
            message='Outbox message was marked as dead.',
            changed=True,
            result={'outbox_status': payload.get('status'), 'last_error': payload.get('last_error', '')},
        )

    def _reprocess_webhook(self, *, entity_type: str, entity_id: str, force: bool) -> RepairResult:
        if entity_type != 'payment_webhook':
            raise ValidationError({'entity_type': 'reprocess_webhook requires entity_type=payment_webhook.'})
        from apps.payments.models import PaymentWebhookEvent
        from apps.payments.services import PaymentWebhookService

        event = PaymentWebhookEvent.objects.get(pk=entity_id)
        if event.status == PaymentWebhookEvent.Status.PROCESSED and not force:
            return RepairResult(
                action='reprocess_webhook',
                status='skipped',
                entity_type=entity_type,
                entity_id=entity_id,
                message='Webhook is already processed. Pass force=true to reprocess it.',
                changed=False,
                result={'webhook_status': event.status, 'processed_at': event.processed_at},
            )

        if force:
            event.status = PaymentWebhookEvent.Status.RECEIVED
            event.processed_at = None
            event.error_message = ''
            event.save(update_fields=['status', 'processed_at', 'error_message', 'updated_at'])

        updated = PaymentWebhookService.handle(
            provider=event.provider,
            event_type=event.event_type,
            external_event_id=event.external_event_id,
            payload=event.payload or {},
            headers=event.headers or {},
            signature=event.signature or '',
            raw_payload_hash=event.raw_payload_hash or '',
            verify_signature=False,
        )
        return RepairResult(
            action='reprocess_webhook',
            status='processed' if updated.status == PaymentWebhookEvent.Status.PROCESSED else updated.status,
            entity_type=entity_type,
            entity_id=entity_id,
            message='Webhook reprocessing finished.',
            changed=True,
            result={
                'webhook_status': updated.status,
                'payment_id': _id(updated.payment_id),
                'processed_at': updated.processed_at,
                'attempts': updated.attempts,
                'error_message': updated.error_message,
            },
        )

    @transaction.atomic
    def _grant_order_access(self, *, entity_type: str, entity_id: str, force: bool) -> RepairResult:
        if entity_type != 'order':
            raise ValidationError({'entity_type': 'grant_order_access requires entity_type=order.'})
        from apps.commerce.services import CommerceFinalizationService
        from apps.entitlements.models import EntitlementStatus
        from apps.orders.models import Order, OrderStatus
        from apps.payments.models import PaymentStatus

        order = Order.objects.select_for_update().prefetch_related('items').get(pk=entity_id)
        active_count = order.granted_entitlements.filter(status=EntitlementStatus.ACTIVE).count()
        if active_count and not force:
            return RepairResult(
                action='grant_order_access',
                status='skipped',
                entity_type=entity_type,
                entity_id=entity_id,
                message='Order already has active entitlement.',
                changed=False,
                result={'active_entitlement_count': active_count, 'order_status': order.status},
            )
        payment = order.payments.filter(status=PaymentStatus.SUCCEEDED).order_by('-confirmed_at', '-updated_at').first()
        if not payment and not force:
            raise ValidationError({'payment': 'A succeeded payment is required before granting access. Pass force=true only for manual/admin grants.'})
        if order.status not in {OrderStatus.PAID, OrderStatus.COMPLETED}:
            if not force:
                raise ValidationError({'order': f'Order status must be paid/completed before granting access. Current status: {order.status}'})
            order.status = OrderStatus.PAID
            order.paid_at = order.paid_at or timezone.now()
            order.save(update_fields=['status', 'paid_at', 'updated_at'])
        if order.status == OrderStatus.COMPLETED and not active_count:
            # CommerceFinalizationService is idempotent and returns early for completed orders,
            # so temporarily move the order back to paid to regenerate the missing access.
            order.status = OrderStatus.PAID
            order.save(update_fields=['status', 'updated_at'])
        CommerceFinalizationService.finalize_paid_order(order=order, payment=payment)
        order.refresh_from_db()
        active_count = order.granted_entitlements.filter(status=EntitlementStatus.ACTIVE).count()
        return RepairResult(
            action='grant_order_access',
            status='completed',
            entity_type=entity_type,
            entity_id=entity_id,
            message='Order access finalization was executed.',
            changed=True,
            result={
                'order_status': order.status,
                'payment_id': _id(getattr(payment, 'id', '')),
                'active_entitlement_count': active_count,
            },
        )

    @transaction.atomic
    def _revoke_entitlement(self, *, entity_type: str, entity_id: str, reason: str, force: bool) -> RepairResult:
        if entity_type != 'entitlement':
            raise ValidationError({'entity_type': 'revoke_entitlement requires entity_type=entitlement.'})
        from apps.entitlements.models import Entitlement, EntitlementStatus
        from apps.events.services import DomainEventService

        entitlement = Entitlement.objects.select_for_update().get(pk=entity_id)
        if entitlement.status != EntitlementStatus.ACTIVE and not force:
            return RepairResult(
                action='revoke_entitlement',
                status='skipped',
                entity_type=entity_type,
                entity_id=entity_id,
                message='Entitlement is not active.',
                changed=False,
                result={'entitlement_status': entitlement.status},
            )
        previous_status = entitlement.status
        entitlement.status = EntitlementStatus.REVOKED
        metadata = dict(entitlement.metadata or {})
        metadata['reconciliation_repair'] = {'reason': reason, 'revoked_at': timezone.now().isoformat()}
        entitlement.metadata = metadata
        entitlement.save(update_fields=['status', 'metadata', 'updated_at'])
        DomainEventService().emit(
            event_type='entitlement.revoked',
            aggregate_type='entitlement',
            aggregate_id=str(entitlement.id),
            idempotency_key=f'entitlement:{entitlement.id}:reconciliation_revoked',
            payload={
                'entitlement_id': str(entitlement.id),
                'user_id': str(entitlement.user_id),
                'previous_status': previous_status,
                'status': entitlement.status,
                'reason': reason,
            },
        )
        return RepairResult(
            action='revoke_entitlement',
            status='completed',
            entity_type=entity_type,
            entity_id=entity_id,
            message='Entitlement was revoked.',
            changed=True,
            result={'previous_status': previous_status, 'entitlement_status': entitlement.status},
        )

    @transaction.atomic
    def _project_payout_accrual(self, *, entity_type: str, entity_id: str, force: bool) -> RepairResult:
        if entity_type != 'payment':
            raise ValidationError({'entity_type': 'project_payout_accrual requires entity_type=payment.'})
        from apps.payments.models import Payment, PaymentStatus
        from apps.payments.services import PaymentService
        from apps.payouts.models import PayoutLedgerEntry
        from apps.payouts.services import PayoutService

        payment = Payment.objects.select_for_update().select_related('order').get(pk=entity_id)
        existing = PayoutLedgerEntry.objects.filter(entry_type=PayoutLedgerEntry.EntryType.ACCRUAL, source_type='payment', source_id=payment.id).first()
        if existing and not force:
            return RepairResult(
                action='project_payout_accrual',
                status='skipped',
                entity_type=entity_type,
                entity_id=entity_id,
                message='Payment already has payout accrual.',
                changed=False,
                result={'ledger_entry_id': str(existing.id), 'payment_status': payment.status},
            )
        if payment.status != PaymentStatus.SUCCEEDED and not force:
            raise ValidationError({'payment': f'Cannot project payout accrual for non-succeeded payment: {payment.status}'})
        trainer_id = PaymentService._extract_trainer_id(payment)
        if not trainer_id:
            raise ValidationError({'trainer_id': 'Could not resolve trainer id from payment/order metadata.'})
        _platform_fee, trainer_net = PaymentService._split_amounts(payment.amount)
        wallet = PayoutService.accrue_from_payment(trainer_id=trainer_id, payment=payment, amount=trainer_net)
        provider_payload = dict(payment.provider_payload or {})
        provider_payload.update({'payout_accrued': True, 'trainer_net': str(trainer_net), 'trainer_id': str(trainer_id), 'reconciliation_projected_at': timezone.now().isoformat()})
        payment.provider_payload = provider_payload
        payment.save(update_fields=['provider_payload', 'updated_at'])
        return RepairResult(
            action='project_payout_accrual',
            status='completed',
            entity_type=entity_type,
            entity_id=entity_id,
            message='Payout accrual was projected from succeeded payment.',
            changed=True,
            result={'trainer_id': str(trainer_id), 'trainer_net': trainer_net, 'wallet_id': wallet.id, 'available_amount': wallet.available_amount},
        )

    @transaction.atomic
    def _reverse_payout_accrual(self, *, entity_type: str, entity_id: str, reason: str, force: bool) -> RepairResult:
        from apps.payments.models import Payment
        from apps.payouts.models import PayoutLedgerEntry
        from apps.payouts.services import PayoutService

        if entity_type == 'payment':
            payment = Payment.objects.select_for_update().get(pk=entity_id)
        elif entity_type == 'payout_ledger':
            entry = PayoutLedgerEntry.objects.select_related('wallet', 'wallet__trainer').get(pk=entity_id)
            if entry.source_type != 'payment':
                raise ValidationError({'payout_ledger': 'Only payment accrual ledger entries can be reversed by this action.'})
            payment = Payment.objects.select_for_update().get(pk=entry.source_id)
        else:
            raise ValidationError({'entity_type': 'reverse_payout_accrual requires entity_type=payment or payout_ledger.'})

        existing_reversal = PayoutLedgerEntry.objects.filter(entry_type=PayoutLedgerEntry.EntryType.REVERSAL, source_type='payment_reconciliation_reversal', source_id=payment.id).first()
        if existing_reversal and not force:
            return RepairResult(
                action='reverse_payout_accrual',
                status='skipped',
                entity_type=entity_type,
                entity_id=entity_id,
                message='Payment already has reconciliation payout reversal.',
                changed=False,
                result={'ledger_entry_id': str(existing_reversal.id), 'payment_id': str(payment.id)},
            )
        reversal = PayoutService.reverse_payment_accrual(
            payment=payment,
            source_type='payment_reconciliation_reversal',
            reversal_status='reconciliation_reversed',
        )
        return RepairResult(
            action='reverse_payout_accrual',
            status='completed',
            entity_type=entity_type,
            entity_id=entity_id,
            message='Payout accrual reversal was executed.',
            changed=True,
            result={'payment_id': str(payment.id), 'reason': reason, 'reversal': reversal},
        )


def run_reconciliation_repair(**kwargs) -> dict[str, Any]:
    return ReconciliationRepairService().execute(**kwargs)
