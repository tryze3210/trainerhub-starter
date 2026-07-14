from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol
import hashlib
from pathlib import Path
from urllib.parse import quote

from django.conf import settings


@dataclass(slots=True)
class StoredArtifact:
    storage_key: str
    url: str
    size_bytes: int
    etag: str
    content_type: str


class ArtifactStorage(Protocol):
    def put_bytes(self, *, storage_key: str, content: bytes, content_type: str) -> StoredArtifact:
        ...

    def build_signed_download_url(self, *, storage_key: str, expires_in: timedelta) -> str:
        ...


class LocalArtifactStorage:
    """Filesystem-backed artifact storage for local and single-node deployments."""

    def __init__(self, *, root: str | Path | None = None, base_url: str | None = None) -> None:
        default_root = Path(getattr(settings, "BASE_DIR", Path.cwd())) / "media" / "finance-documents"
        self.root = Path(root or getattr(settings, "FINANCE_DOCUMENT_ARTIFACT_ROOT", default_root))
        self.base_url = (base_url or getattr(settings, "FINANCE_DOCUMENT_ARTIFACT_BASE_URL", "/media/finance-documents/")).rstrip("/") + "/"

    def _path_for_key(self, storage_key: str) -> Path:
        relative = Path(storage_key)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid finance document storage key")
        return self.root / relative

    def put_bytes(self, *, storage_key: str, content: bytes, content_type: str) -> StoredArtifact:
        path = self._path_for_key(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        etag = hashlib.sha256(content).hexdigest()
        relative_url = quote(storage_key)
        return StoredArtifact(
            storage_key=storage_key,
            url=f"{self.base_url}{relative_url}",
            size_bytes=len(content),
            etag=etag,
            content_type=content_type,
        )

    def build_signed_download_url(self, *, storage_key: str, expires_in: timedelta) -> str:
        self._path_for_key(storage_key)
        seconds = int(expires_in.total_seconds())
        relative_url = quote(storage_key)
        return f"{self.base_url}{relative_url}?download=1&expires_in={seconds}"


DummyArtifactStorage = LocalArtifactStorage
