from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class RenderedArtifact:
    content: bytes
    content_type: str
    extension: str


class PDFRenderer(Protocol):
    def render_html_to_pdf(self, *, html: str) -> RenderedArtifact:
        ...


class WeasyPrintPDFRenderer:
    """
    Production seam. Install weasyprint in backend image and use this implementation.
    """

    def render_html_to_pdf(self, *, html: str) -> RenderedArtifact:
        from weasyprint import HTML  # type: ignore

        pdf_bytes = HTML(string=html).write_pdf()
        return RenderedArtifact(
            content=pdf_bytes,
            content_type="application/pdf",
            extension="pdf",
        )
