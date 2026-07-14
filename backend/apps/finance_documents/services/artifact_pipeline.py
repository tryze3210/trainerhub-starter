from __future__ import annotations

from django.utils import timezone

from .download_urls import FinanceDocumentDownloadURLService
from .pdf_renderer import WeasyPrintPDFRenderer
from .rendering import FinanceDocumentRenderer
from .storage import DummyArtifactStorage


class FinanceDocumentArtifactPipeline:
    def __init__(self, *, renderer=None, storage=None):
        self.renderer = renderer or WeasyPrintPDFRenderer()
        self.document_renderer = FinanceDocumentRenderer()
        self.storage = storage or DummyArtifactStorage()
        self.download_urls = FinanceDocumentDownloadURLService(self.storage)

    def build_and_store(self, *, document):
        html = document.rendered_html or self.document_renderer.render(document)
        rendered = self.renderer.render_html_to_pdf(html=html)
        storage_key = f"finance-documents/{document.document_type}/{document.id}.{rendered.extension}"
        stored = self.storage.put_bytes(
            storage_key=storage_key,
            content=rendered.content,
            content_type=rendered.content_type,
        )
        document.artifact_path = stored.url
        document.artifact_storage_key = stored.storage_key
        document.artifact_size_bytes = stored.size_bytes
        document.artifact_etag = stored.etag
        document.artifact_content_type = stored.content_type
        document.artifact_generated_at = timezone.now()
        document.save(update_fields=[
            "artifact_path",
            "artifact_storage_key",
            "artifact_size_bytes",
            "artifact_etag",
            "artifact_content_type",
            "artifact_generated_at",
            "updated_at",
        ])
        return document
