from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.finance.domain.enums import (
    DiscrepancyType,
    ReconciliationSessionStatus,
    SettlementStatus,
)
from apps.finance.models import ReconciliationDiscrepancy, ReconciliationSession, SettlementTransaction
from apps.finance.services.outbox_service import FinanceOutboxService


class ReconciliationService:
    def __init__(self, gateway):
        self.gateway = gateway

    @transaction.atomic
    def run(self, *, date_from, date_to, started_by=None):
        session = ReconciliationSession.objects.create(
            provider=self.gateway.provider_code,
            date_from=date_from,
            date_to=date_to,
            started_by=started_by,
            raw_import_meta={},
        )
        try:
            provider_rows = self.gateway.fetch_transactions(date_from=date_from, date_to=date_to)
            internal_map = {
                tx.provider_reference: tx
                for tx in SettlementTransaction.objects.filter(
                    provider=self.gateway.provider_code,
                    requested_at__gte=date_from,
                    requested_at__lt=date_to,
                )
            }
            provider_seen = set()
            mismatch_count = 0

            for row in provider_rows:
                ref = row["provider_reference"]
                provider_seen.add(ref)
                tx = internal_map.get(ref)
                if not tx:
                    mismatch_count += 1
                    self._discrepancy(
                        session=session,
                        discrepancy_type=DiscrepancyType.MISSING_INTERNAL,
                        provider_reference=ref,
                        provider_amount=Decimal(row["amount"]),
                        provider_status=row["status"],
                        details=row,
                    )
                    continue

                if Decimal(tx.amount) != Decimal(row["amount"]):
                    mismatch_count += 1
                    self._discrepancy(
                        session=session,
                        discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
                        settlement_transaction=tx,
                        provider_reference=ref,
                        internal_amount=tx.amount,
                        provider_amount=Decimal(row["amount"]),
                        internal_status=tx.status,
                        provider_status=row["status"],
                        details=row,
                    )

                normalized_provider_status = self._normalize_provider_status(row["status"])
                if tx.status != normalized_provider_status:
                    mismatch_count += 1
                    self._discrepancy(
                        session=session,
                        discrepancy_type=DiscrepancyType.STATUS_MISMATCH,
                        settlement_transaction=tx,
                        provider_reference=ref,
                        internal_amount=tx.amount,
                        provider_amount=Decimal(row["amount"]),
                        internal_status=tx.status,
                        provider_status=row["status"],
                        details=row,
                    )

            for ref, tx in internal_map.items():
                if ref not in provider_seen:
                    mismatch_count += 1
                    self._discrepancy(
                        session=session,
                        discrepancy_type=DiscrepancyType.MISSING_PROVIDER,
                        settlement_transaction=tx,
                        provider_reference=ref,
                        internal_amount=tx.amount,
                        internal_status=tx.status,
                        details={"requested_at": tx.requested_at.isoformat()},
                    )

            session.status = ReconciliationSessionStatus.COMPLETED
            session.completed_at = timezone.now()
            session.summary = {
                "provider_rows": len(provider_rows),
                "internal_rows": len(internal_map),
                "mismatch_count": mismatch_count,
            }
            session.save(update_fields=["status", "completed_at", "summary", "updated_at"])

            FinanceOutboxService.publish(
                topic="finance.reconciliation.completed",
                aggregate_type="reconciliation_session",
                aggregate_id=str(session.id),
                payload=session.summary | {"session_id": str(session.id), "provider": session.provider},
            )
            return session
        except Exception as exc:
            session.status = ReconciliationSessionStatus.FAILED
            session.failed_at = timezone.now()
            session.summary = {"error": str(exc)}
            session.save(update_fields=["status", "failed_at", "summary", "updated_at"])
            raise

    def _discrepancy(self, **kwargs):
        return ReconciliationDiscrepancy.objects.create(**kwargs)

    def _normalize_provider_status(self, provider_status: str) -> str:
        mapping = {
            "paid": SettlementStatus.SETTLED,
            "settled": SettlementStatus.SETTLED,
            "processing": SettlementStatus.PROCESSING,
            "failed": SettlementStatus.FAILED,
            "reversed": SettlementStatus.REVERSED,
            "sent": SettlementStatus.SENT,
        }
        return mapping.get(provider_status.lower(), SettlementStatus.PROCESSING)
