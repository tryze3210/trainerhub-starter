from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone

from .adapters import adapter_registry
from .constants import (
    EXPORT_RUN_STATUS_DELIVERED,
    EXPORT_RUN_STATUS_EXPORTED,
    EXPORT_RUN_STATUS_FAILED,
    EXPORT_RUN_STATUS_QUEUED,
    JOURNAL_BATCH_STATUS_FINALIZED,
)
from .exceptions import AccountMappingError, ExportRunStateError, JournalBatchStateError
from .models import (
    AccountMappingRule,
    ExportDeliveryAttempt,
    GLExportRun,
    JournalBatch,
    JournalEntry,
    JournalLine,
)


@dataclass(slots=True)
class PostingLine:
    account_code: str
    debit_amount: Decimal
    credit_amount: Decimal
    description: str
    dimensions: dict


class AccountMappingService:
    def resolve_account(self, *, system, target_type: str, source_code: str, on_date):
        rule = (
            AccountMappingRule.objects.select_related("account")
            .filter(
                system=system,
                target_type=target_type,
                source_code=source_code,
                effective_from__lte=on_date,
                is_active=True,
            )
            .filter(models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=on_date))
            .order_by("priority", "id")
            .first()
        )
        if not rule:
            raise AccountMappingError(f"No mapping for {target_type}:{source_code} on {on_date}")
        return rule.account


class JournalBatchBuilderService:
    @transaction.atomic
    def build_from_period_snapshot(self, *, system, period, snapshot, created_by) -> JournalBatch:
        batch = JournalBatch.objects.create(
            system=system,
            period=period,
            snapshot=snapshot,
            batch_number=f"JB-{period.id}-{uuid.uuid4().hex[:10].upper()}",
            description=f"GL export journal for period {period.id}",
            currency=system.base_currency,
            created_by=created_by,
            metadata={"snapshot_id": snapshot.id},
        )

        ledger_entries = (
            snapshot.ledger_entries.all()
            if hasattr(snapshot, "ledger_entries")
            else []
        )
        mapping_service = AccountMappingService()
        entry_number = 0
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")

        for ledger_entry in ledger_entries:
            entry_number += 1
            journal_entry = JournalEntry.objects.create(
                batch=batch,
                entry_number=entry_number,
                entry_date=ledger_entry.posted_at.date(),
                reference=ledger_entry.reference,
                description=ledger_entry.description,
                source_ledger_entry=ledger_entry,
                source_document=getattr(ledger_entry, "document", None),
                metadata={"ledger_entry_id": ledger_entry.id},
            )

            debit_account = mapping_service.resolve_account(
                system=system,
                target_type="ledger_account",
                source_code=f"DEBIT:{ledger_entry.debit_account_code}",
                on_date=ledger_entry.posted_at.date(),
            )
            credit_account = mapping_service.resolve_account(
                system=system,
                target_type="ledger_account",
                source_code=f"CREDIT:{ledger_entry.credit_account_code}",
                on_date=ledger_entry.posted_at.date(),
            )
            amount = ledger_entry.amount

            JournalLine.objects.create(
                entry=journal_entry,
                line_number=1,
                account=debit_account,
                debit_amount=amount,
                credit_amount=Decimal("0.00"),
                currency=ledger_entry.currency,
                description=ledger_entry.description,
                dimensions={"trainer_id": getattr(ledger_entry, "trainer_id", None)},
            )
            JournalLine.objects.create(
                entry=journal_entry,
                line_number=2,
                account=credit_account,
                debit_amount=Decimal("0.00"),
                credit_amount=amount,
                currency=ledger_entry.currency,
                description=ledger_entry.description,
                dimensions={"trainer_id": getattr(ledger_entry, "trainer_id", None)},
            )
            total_debit += amount
            total_credit += amount

        batch.total_debit = total_debit
        batch.total_credit = total_credit
        batch.mark_finalized()
        batch.save(update_fields=["total_debit", "total_credit", "status", "finalized_at", "updated_at"])
        return batch


class GLExportService:
    @transaction.atomic
    def create_export_run(self, *, journal_batch: JournalBatch, created_by, export_format="json", supersedes=None) -> GLExportRun:
        if journal_batch.status != JOURNAL_BATCH_STATUS_FINALIZED:
            raise JournalBatchStateError("Only finalized journal batches can be exported")

        run = GLExportRun.objects.create(
            system=journal_batch.system,
            period=journal_batch.period,
            journal_batch=journal_batch,
            export_format=export_format,
            run_number=f"ER-{journal_batch.id}-{uuid.uuid4().hex[:8].upper()}",
            idempotency_key=f"gl-export:{journal_batch.id}:{uuid.uuid4().hex}",
            created_by=created_by,
            supersedes=supersedes,
        )
        return run

    @transaction.atomic
    def queue_export(self, *, export_run: GLExportRun) -> GLExportRun:
        if export_run.status != "draft":
            raise ExportRunStateError("Only draft export runs can be queued")
        export_run.status = EXPORT_RUN_STATUS_QUEUED
        export_run.save(update_fields=["status", "updated_at"])
        return export_run

    @transaction.atomic
    def render_export_payload(self, *, export_run: GLExportRun) -> GLExportRun:
        adapter = adapter_registry.get(export_run.system.adapter_key)
        payload = adapter.build_export_payload(export_run)
        filename, raw, checksum = adapter.render_file(export_run)
        export_run.payload = payload
        export_run.file_path = f"accounting_exports/{filename}"
        export_run.checksum = checksum
        export_run.status = EXPORT_RUN_STATUS_EXPORTED
        export_run.exported_at = timezone.now()
        export_run.save(update_fields=["payload", "file_path", "checksum", "status", "exported_at", "updated_at"])
        export_run.journal_batch.mark_exported()
        export_run.journal_batch.save(update_fields=["status", "exported_at", "updated_at"])
        return export_run

    @transaction.atomic
    def deliver_export(self, *, export_run: GLExportRun) -> GLExportRun:
        if export_run.status != EXPORT_RUN_STATUS_EXPORTED:
            raise ExportRunStateError("Only exported runs can be delivered")
        adapter = adapter_registry.get(export_run.system.adapter_key)
        result = adapter.deliver(export_run)
        attempt_no = export_run.delivery_attempts.count() + 1
        ExportDeliveryAttempt.objects.create(
            export_run=export_run,
            attempt_number=attempt_no,
            request_payload={"run_number": export_run.run_number},
            response_payload=result.response_payload or {},
            is_success=result.is_success,
            error_message=result.error_message,
        )
        if result.is_success:
            export_run.status = EXPORT_RUN_STATUS_DELIVERED
            export_run.delivered_at = timezone.now()
            export_run.failure_reason = ""
        else:
            export_run.status = EXPORT_RUN_STATUS_FAILED
            export_run.failure_reason = result.error_message
        export_run.save(update_fields=["status", "delivered_at", "failure_reason", "updated_at"])
        return export_run


class ClosingAccountingHandoffService:
    @transaction.atomic
    def handoff_closed_period(self, *, system, period, snapshot, created_by) -> GLExportRun:
        batch = JournalBatchBuilderService().build_from_period_snapshot(
            system=system,
            period=period,
            snapshot=snapshot,
            created_by=created_by,
        )
        export_run = GLExportService().create_export_run(
            journal_batch=batch,
            created_by=created_by,
        )
        GLExportService().queue_export(export_run=export_run)
        GLExportService().render_export_payload(export_run=export_run)
        GLExportService().deliver_export(export_run=export_run)
        return export_run
