from django.db.models import Sum

from .models import GLExportRun, JournalBatch, JournalEntry


def list_journal_batches(*, system_id=None, period_id=None, status=None):
    qs = JournalBatch.objects.select_related("system", "period", "snapshot", "created_by")
    if system_id:
        qs = qs.filter(system_id=system_id)
    if period_id:
        qs = qs.filter(period_id=period_id)
    if status:
        qs = qs.filter(status=status)
    return qs.order_by("-created_at")


def get_journal_batch_totals(batch):
    return batch.entries.aggregate(entry_count=Sum("id"))


def list_export_runs(*, system_id=None, period_id=None, status=None):
    qs = GLExportRun.objects.select_related("system", "period", "journal_batch", "created_by")
    if system_id:
        qs = qs.filter(system_id=system_id)
    if period_id:
        qs = qs.filter(period_id=period_id)
    if status:
        qs = qs.filter(status=status)
    return qs.order_by("-created_at")


def get_batch_source_entries(batch_id):
    return JournalEntry.objects.filter(batch_id=batch_id).select_related("source_ledger_entry", "source_document")
