"""Write validated MVP agent packages."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from article2agentspec.exceptions import ValidationFailure, WriteError
from article2agentspec.extraction.base import PackageDraft
from article2agentspec.validation.validators import ValidationResult
from schemas.article2agentspec.models import Manifest, ValidationStatus


REQUIRED_PACKAGE_FILES = [
    "manifest.yaml",
    "source_metadata.yaml",
    "source_text.md",
    "agent_spec.yaml",
    "workflow.json",
    "tools.json",
    "eval_config.yaml",
    "prompts.md",
    "implementation_notes.md",
    "evidence_report.md",
]


def write_package(
    draft: PackageDraft,
    output_root: str | Path,
    validation_result: ValidationResult,
    *,
    debug: bool = False,
) -> Path:
    """Write an already validated draft package to disk."""
    if not validation_result.passed:
        raise ValidationFailure("cannot write package because validation failed")

    package_dir = Path(output_root) / draft.source_stem
    try:
        package_dir.mkdir(parents=True, exist_ok=True)
        manifest = _build_manifest(draft, validation_result)

        _write_yaml(package_dir / "manifest.yaml", manifest)
        _write_yaml(package_dir / "source_metadata.yaml", draft.source_metadata)
        _write_text(package_dir / "source_text.md", draft.source_text_md)
        _write_yaml(package_dir / "agent_spec.yaml", draft.agent_spec)
        _write_json(package_dir / "workflow.json", draft.workflow)
        _write_json(package_dir / "tools.json", draft.tools)
        _write_yaml(package_dir / "eval_config.yaml", draft.eval_config)
        _write_text(package_dir / "prompts.md", draft.prompts_md)
        _write_text(package_dir / "implementation_notes.md", draft.implementation_notes_md)
        _write_text(package_dir / "evidence_report.md", draft.evidence_report_md)

        if debug:
            _write_debug_artifacts(package_dir, draft, validation_result)
    except OSError as exc:
        raise WriteError(f"failed to write package: {package_dir}") from exc
    except ValidationError as exc:
        raise ValidationFailure(f"manifest failed validation: {exc}") from exc

    return package_dir


def _build_manifest(draft: PackageDraft, validation_result: ValidationResult) -> Manifest:
    return Manifest(
        source_file=draft.source_metadata.source.file_name,
        generated_at=_utc_now_iso(),
        files=REQUIRED_PACKAGE_FILES.copy(),
        validation=ValidationStatus(
            status="passed",
            warnings=validation_result.warnings,
        ),
    )


def _write_yaml(path: Path, value: BaseModel) -> None:
    path.write_text(
        yaml.safe_dump(value.model_dump(mode="json"), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _write_json(path: Path, value: BaseModel | dict[str, Any]) -> None:
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json")
    else:
        payload = value
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")


def _write_debug_artifacts(package_dir: Path, draft: PackageDraft, validation_result: ValidationResult) -> None:
    debug_dir = package_dir / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    for file_name, payload in draft.debug_artifacts.items():
        _write_json(debug_dir / file_name, payload)
    _write_json(debug_dir / "validation_report.json", validation_result.to_debug_dict())


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
