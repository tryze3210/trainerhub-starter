from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.finance.domain.enums import PayoutBatchStatus, SettlementStatus
from apps.finance.models import ProviderWebhookInbox, SettlementTransaction
from apps.finance.services.outbox_service import FinanceOutboxService


class ProviderWebhookService:
    def __init__(self, gateway):
        self.gateway = gateway

    @transaction.atomic
    def handle_event(self, *, headers: dict, payload: dict):
        event = self.gateway.parse_webhook(headers=headers, payload=payload)

        inbox, created = ProviderWebhookInbox.objects.get_or_create(
            event_id=event.event_id,
            defaults={
                "provider": event.provider,
                "event_type": event.event_type,
                "payload": event.payload,
                "signature_valid": True,
            },
        )
        if not created and inbox.processed_at:
            return inbox

        tx = SettlementTransaction.objects.filter(
            provider=event.provider,
            provider_reference=event.provider_reference,
        ).select_related("payout_batch").first()
        if not tx:
            inbox.processing_error = "Settlement transaction not found"
            inbox.save(update_fields=["processing_error", "updated_at"])
            raise ValueError("Settlement transaction not found")

        mapped_status = self._map_status(event.status)
        tx.status = mapped_status
        if mapped_status == SettlementStatus.SETTLED:
            tx.settled_at = timezone.now()
        elif mapped_status == SettlementStatus.FAILED:
            tx.failed_at = timezone.now()
        tx.provider_payload = event.payload
        tx.save(update_fields=["status", "settled_at", "failed_at", "provider_payload", "updated_at"])

        self._cascade_payout_batch_status(tx)

        inbox.processed_at = timezone.now()
        inbox.processing_error = ""
        inbox.save(update_fields=["processed_at", "processing_error", "updated_at"])

        FinanceOutboxService.publish(
            topic="finance.settlement_transaction.updated",
            aggregate_type="settlement_transaction",
            aggregate_id=str(tx.id),
            payload={
                "settlement_transaction_id": str(tx.id),
                "provider_reference": tx.provider_reference,
                "status": tx.status,
            },
        )
        return inbox

    def _map_status(self, provider_status: str) -> str:
        mapping = {
            "processing": SettlementStatus.PROCESSING,
            "paid": SettlementStatus.SETTLED,
            "settled": SettlementStatus.SETTLED,
            "failed": SettlementStatus.FAILED,
            "reversed": SettlementStatus.REVERSED,
        }
        return mapping.get(provider_status.lower(), SettlementStatus.PROCESSING)

    def _cascade_payout_batch_status(self, tx):
        batch = tx.payout_batch
        if not batch:
            return

        statuses = list(batch.settlement_transactions.values_list("status", flat=True))
        if statuses and all(status == SettlementStatus.SETTLED for status in statuses):
            batch.status = PayoutBatchStatus.PAID
            batch.paid_at = timezone.now()
            batch.save(update_fields=["status", "paid_at", "updated_at"])
        elif any(status == SettlementStatus.FAILED for status in statuses):
            batch.status = PayoutBatchStatus.FAILED
            batch.save(update_fields=["status", "updated_at"])
        else:
            batch.status = PayoutBatchStatus.PROCESSING
            batch.save(update_fields=["status", "updated_at"])
