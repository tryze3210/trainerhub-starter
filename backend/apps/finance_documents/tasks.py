from celery import shared_task
from django.apps import apps

from .services.artifact_pipeline import FinanceDocumentArtifactPipeline
from .services.download_urls import FinanceDocumentDownloadURLService
from .services.email_delivery import FinanceDocumentEmailDeliveryService
from .services.storage import DummyArtifactStorage


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def generate_finance_document_artifact(self, document_id: str):
    FinanceDocument = apps.get_model("finance_documents", "FinanceDocument")
    document = FinanceDocument.objects.get(id=document_id)
    pipeline = FinanceDocumentArtifactPipeline()
    pipeline.build_and_store(document=document)
    return str(document.id)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def deliver_finance_document_email(self, document_id: str):
    FinanceDocument = apps.get_model("finance_documents", "FinanceDocument")
    FinanceDocumentDelivery = apps.get_model("finance_documents", "FinanceDocumentDelivery")
    document = FinanceDocument.objects.select_related("trainer").get(id=document_id)
    storage = DummyArtifactStorage()
    download_url = FinanceDocumentDownloadURLService(storage).build_url(document=document)
    recipient_email = getattr(getattr(document, "trainer", None), "email", "")
    if not recipient_email:
        raise ValueError("Trainer email is missing for finance document delivery")
    FinanceDocumentEmailDeliveryService().send_document_ready(
        document=document,
        recipient_email=recipient_email,
        download_url=download_url,
        delivery_model=FinanceDocumentDelivery,
    )
    return str(document.id)
