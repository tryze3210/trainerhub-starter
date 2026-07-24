from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.finance.domain.enums import PayoutBatchStatus, SettlementDirection, SettlementStatus
from apps.finance.models import SettlementTransaction
from apps.finance.services.outbox_service import FinanceOutboxService


class PayoutExportService:
    def __init__(self, gateway):
        self.gateway = gateway

    @transaction.atomic
    def export_batch(self, *, payout_batch):
        if payout_batch.status != PayoutBatchStatus.DRAFT:
            raise ValueError("Only draft payout batches can be exported")

        items = list(payout_batch.items.select_related("trainer"))
        result = self.gateway.export_payout_batch(batch=payout_batch, items=items)

        payout_batch.status = PayoutBatchStatus.EXPORTED
        payout_batch.external_reference = result.provider_batch_reference
        payout_batch.exported_at = timezone.now()
        payout_batch.save(update_fields=["status", "external_reference", "exported_at", "updated_at"])

        for item, exported in zip(items, result.items, strict=False):
            SettlementTransaction.objects.create(
                provider=self.gateway.provider_code,
                direction=SettlementDirection.PAYOUT,
                status=SettlementStatus.SENT,
                payout_batch=payout_batch,
                payout_item=item,
                trainer=item.trainer,
                amount=item.amount,
                currency=getattr(item, "currency", "RUB"),
                provider_reference=exported["provider_reference"],
                provider_batch_reference=result.provider_batch_reference,
                idempotency_key=f"payout-export:{payout_batch.id}:{item.id}",
                provider_payload=exported,
                metadata={
                    "payout_batch_id": str(payout_batch.id),
                    "payout_item_id": str(item.id),
                },
            )

        FinanceOutboxService.publish(
            topic="finance.payout_batch.exported",
            aggregate_type="payout_batch",
            aggregate_id=str(payout_batch.id),
            payload={
                "payout_batch_id": str(payout_batch.id),
                "provider": self.gateway.provider_code,
                "provider_batch_reference": result.provider_batch_reference,
                "items_count": len(result.items),
            },
        )

        return payout_batch
