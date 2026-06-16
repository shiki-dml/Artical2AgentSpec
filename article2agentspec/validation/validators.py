"""Validation for package schema and evidence references."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from article2agentspec.extraction.base import PackageDraft
from schemas.article2agentspec.models import AgentSpec, EvalConfig, SourceMetadata, ToolsSpec, WorkflowSpec


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating a draft package before writing."""

    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_debug_dict(self) -> dict[str, Any]:
        """Return JSON-serializable validation details."""
        return {
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def validate_package(draft: PackageDraft) -> ValidationResult:
    """Validate structured package data and evidence references."""
    errors: list[str] = []
    warnings: list[str] = []

    _validate_model("source_metadata", SourceMetadata, draft.source_metadata, errors)
    _validate_model("agent_spec", AgentSpec, draft.agent_spec, errors)
    _validate_model("workflow", WorkflowSpec, draft.workflow, errors)
    _validate_model("tools", ToolsSpec, draft.tools, errors)
    _validate_model("eval_config", EvalConfig, draft.eval_config, errors)

    referenced_ids = _collect_evidence_refs(
        [
            draft.agent_spec.model_dump(mode="json"),
            draft.workflow.model_dump(mode="json"),
            draft.tools.model_dump(mode="json"),
            draft.eval_config.model_dump(mode="json"),
        ]
    )
    missing_refs = sorted(referenced_ids - draft.evidence_ids)
    if missing_refs:
        errors.append(f"unresolved evidence_refs: {', '.join(missing_refs)}")

    return ValidationResult(passed=not errors, errors=errors, warnings=warnings)


def _validate_model(name: str, model_type: type[Any], value: Any, errors: list[str]) -> None:
    try:
        model_type.model_validate(value.model_dump(mode="python"))
    except ValidationError as exc:
        errors.append(f"{name} failed schema validation: {exc}")


def _collect_evidence_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "evidence_refs" and isinstance(item, list):
                refs.update(str(ref) for ref in item)
            else:
                refs.update(_collect_evidence_refs(item))
    elif isinstance(value, list):
        for item in value:
            refs.update(_collect_evidence_refs(item))
    return refs
