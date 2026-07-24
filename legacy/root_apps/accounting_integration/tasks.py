from celery import shared_task

from apps.accounting_integration.models import GLExportRun
from apps.accounting_integration.services import GLExportService


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def render_gl_export_task(self, export_run_id: int) -> None:
    export_run = GLExportRun.objects.select_related("system", "period", "journal_batch").get(id=export_run_id)
    GLExportService().render_export_payload(export_run=export_run)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def deliver_gl_export_task(self, export_run_id: int) -> None:
    export_run = GLExportRun.objects.select_related("system", "period", "journal_batch").get(id=export_run_id)
    GLExportService().deliver_export(export_run=export_run)
