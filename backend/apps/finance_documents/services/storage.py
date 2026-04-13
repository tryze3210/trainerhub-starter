from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol
import hashlib


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


class DummyArtifactStorage:
    """
    Integration seam. Replace with VK Cloud S3-compatible storage adapter.
    """

    def put_bytes(self, *, storage_key: str, content: bytes, content_type: str) -> StoredArtifact:
        etag = hashlib.md5(content).hexdigest()
        return StoredArtifact(
            storage_key=storage_key,
            url=f"https://storage.example.invalid/{storage_key}",
            size_bytes=len(content),
            etag=etag,
            content_type=content_type,
        )

    def build_signed_download_url(self, *, storage_key: str, expires_in: timedelta) -> str:
        seconds = int(expires_in.total_seconds())
        return f"https://storage.example.invalid/{storage_key}?signed=1&expires_in={seconds}"
