from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.finance.domain.enums import DiscrepancyStatus, SettlementStatus
from apps.finance.models import ReconciliationDiscrepancy
from apps.finance.services.outbox_service import FinanceOutboxService


class FinanceRepairService:
    @transaction.atomic
    def mark_discrepancy_resolved(self, *, discrepancy: ReconciliationDiscrepancy, resolved_by, notes: str):
        discrepancy.status = DiscrepancyStatus.RESOLVED
        discrepancy.resolution_notes = notes
        discrepancy.resolved_by = resolved_by
        discrepancy.resolved_at = timezone.now()
        discrepancy.save(update_fields=["status", "resolution_notes", "resolved_by", "resolved_at", "updated_at"])

        FinanceOutboxService.publish(
            topic="finance.discrepancy.resolved",
            aggregate_type="reconciliation_discrepancy",
            aggregate_id=str(discrepancy.id),
            payload={
                "discrepancy_id": str(discrepancy.id),
                "resolution_notes": notes,
            },
        )
        return discrepancy

    @transaction.atomic
    def force_settlement_status(self, *, discrepancy: ReconciliationDiscrepancy, target_status: str, resolved_by, notes: str):
        tx = discrepancy.settlement_transaction
        if not tx:
            raise ValueError("Discrepancy has no internal settlement transaction")

        tx.status = target_status
        tx.save(update_fields=["status", "updated_at"])
        return self.mark_discrepancy_resolved(discrepancy=discrepancy, resolved_by=resolved_by, notes=notes)
