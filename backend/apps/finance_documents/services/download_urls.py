from __future__ import annotations

from datetime import timedelta


class FinanceDocumentDownloadURLService:
    def __init__(self, storage):
        self.storage = storage

    def build_url(self, *, document, expires_in_minutes: int = 15) -> str:
        if not getattr(document, "artifact_storage_key", ""):
            raise ValueError("Document artifact is not generated yet")
        return self.storage.build_signed_download_url(
            storage_key=document.artifact_storage_key,
            expires_in=timedelta(minutes=expires_in_minutes),
        )
