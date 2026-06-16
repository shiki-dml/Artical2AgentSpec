"""Pipeline orchestration for parse -> extract -> validate -> write."""

from __future__ import annotations

from pathlib import Path

from article2agentspec.exceptions import ValidationFailure
from article2agentspec.extraction.heuristic import extract_baseline
from article2agentspec.parsing.pdf import parse_pdf
from article2agentspec.validation.validators import validate_package
from article2agentspec.writing.package_writer import write_package


def convert_pdf(source_pdf: str | Path, output_root: str | Path = "outputs", *, debug: bool = False) -> Path:
    """Convert a local PDF into an MVP agent package."""
    parsed = parse_pdf(source_pdf)
    draft = extract_baseline(parsed)
    validation_result = validate_package(draft)
    if not validation_result.passed:
        details = "; ".join(validation_result.errors)
        raise ValidationFailure(f"validation failed: {details}")
    return write_package(draft, output_root, validation_result, debug=debug)
