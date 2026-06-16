"""PDF parsing for local MVP inputs."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from article2agentspec.exceptions import InputError, ParseError
from schemas.article2agentspec.models import ParserMetadata, SourceDocumentMetadata, SourceMetadata


@dataclass(frozen=True)
class ParsedPage:
    """Text extracted from a single PDF page."""

    page_number: int
    text: str


@dataclass(frozen=True)
class ParsedDocument:
    """Parsed PDF text and metadata preserved for downstream stages."""

    source_path: Path
    source_id: str
    file_name: str
    file_sha256: str
    page_count: int
    pages: list[ParsedPage]
    parser: ParserMetadata

    @property
    def source_stem(self) -> str:
        """Return the source file stem used for output package paths."""
        return self.source_path.stem

    def to_source_metadata(self) -> SourceMetadata:
        """Build canonical source metadata for package output."""
        return SourceMetadata(
            source=SourceDocumentMetadata(
                source_id=self.source_id,
                source_type="pdf",
                file_name=self.file_name,
                file_sha256=self.file_sha256,
                page_count=self.page_count,
            ),
            parser=self.parser,
        )

    def to_debug_dict(self) -> dict[str, Any]:
        """Return JSON-serializable parse data for debug output."""
        return {
            "source_id": self.source_id,
            "source_path": str(self.source_path),
            "file_name": self.file_name,
            "file_sha256": self.file_sha256,
            "page_count": self.page_count,
            "parser": self.parser.model_dump(mode="json"),
            "pages": [
                {
                    "page_number": page.page_number,
                    "text": page.text,
                }
                for page in self.pages
            ],
        }


def parse_pdf(source_pdf: str | Path) -> ParsedDocument:
    """Parse a local PDF into page-level text and source metadata."""
    source_path = Path(source_pdf)
    _validate_pdf_path(source_path)

    file_sha256 = _sha256_file(source_path)
    try:
        reader = PdfReader(str(source_path))
        pages = [
            ParsedPage(page_number=index, text=page.extract_text() or "")
            for index, page in enumerate(reader.pages, start=1)
        ]
    except Exception as exc:  # noqa: BLE001 - convert parser errors to domain errors.
        raise ParseError(f"failed to parse PDF: {source_path}") from exc

    return ParsedDocument(
        source_path=source_path,
        source_id="src_001",
        file_name=source_path.name,
        file_sha256=file_sha256,
        page_count=len(pages),
        pages=pages,
        parser=ParserMetadata(
            name="pypdf",
            version=_package_version("pypdf"),
            parsed_at=_utc_now_iso(),
        ),
    )


def _validate_pdf_path(source_path: Path) -> None:
    if not source_path.exists():
        raise InputError(f"input file does not exist: {source_path}")
    if not source_path.is_file():
        raise InputError(f"input path is not a file: {source_path}")
    if source_path.suffix.lower() != ".pdf":
        raise InputError(f"input file is not a PDF: {source_path}")


def _sha256_file(source_path: Path) -> str:
    digest = hashlib.sha256()
    with source_path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_version(package_name: str) -> str | None:
    try:
        return version(package_name)
    except PackageNotFoundError:
        return None


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
