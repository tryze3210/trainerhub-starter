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
    """Render PDFs when WeasyPrint is installed, otherwise persist HTML."""

    def render_html_to_pdf(self, *, html: str) -> RenderedArtifact:
        try:
            from weasyprint import HTML  # type: ignore
        except ImportError:
            return RenderedArtifact(
                content=html.encode("utf-8"),
                content_type="text/html; charset=utf-8",
                extension="html",
            )

        pdf_bytes = HTML(string=html).write_pdf()
        return RenderedArtifact(
            content=pdf_bytes,
            content_type="application/pdf",
            extension="pdf",
        )
