"""Canonical Pydantic models for Article2AgentSpec outputs."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator


SCHEMA_VERSION = "0.1.0"

EvidenceRef: TypeAlias = Annotated[str, Field(min_length=1)]


class FidelityState(str, Enum):
    """Source-fidelity state for an extracted design claim."""

    EXPLICIT = "explicit"
    INFERRED = "inferred"
    MISSING = "missing"
    CONFLICT = "conflict"


class ConflictCandidate(BaseModel):
    """One candidate value preserved for a conflicting source claim."""

    model_config = ConfigDict(extra="forbid")

    value: Any
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    preferred: bool = False
    rationale: str | None = None

    @model_validator(mode="after")
    def validate_candidate(self) -> ConflictCandidate:
        """Require each conflict candidate to be concrete and evidenced."""
        if self.value is None:
            raise ValueError("conflict candidates require a value")
        if not self.evidence_refs:
            raise ValueError("conflict candidates require evidence_refs")
        return self


class Claim(BaseModel):
    """A source-grounded claim with fidelity metadata."""

    model_config = ConfigDict(extra="forbid")

    value: Any | None = None
    fidelity: FidelityState = FidelityState.MISSING
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    rationale: str | None = None
    candidates: list[ConflictCandidate] = Field(default_factory=list)
    conflict_reason: str | None = None
    impact: str | None = None

    @model_validator(mode="after")
    def validate_fidelity_rules(self) -> Claim:
        """Enforce local fidelity rules for a single claim."""
        if self.fidelity is FidelityState.EXPLICIT:
            if self.value is None:
                raise ValueError("explicit claims require a value")
            if not self.evidence_refs:
                raise ValueError("explicit claims require evidence_refs")
            self._reject_conflict_fields("explicit")

        if self.fidelity is FidelityState.INFERRED:
            if self.value is None:
                raise ValueError("inferred claims require a value")
            if not self.evidence_refs:
                raise ValueError("inferred claims require evidence_refs")
            if not self.rationale:
                raise ValueError("inferred claims require rationale")
            self._reject_conflict_fields("inferred")

        if self.fidelity is FidelityState.MISSING:
            if self.value is not None:
                raise ValueError("missing claims must not contain a value")
            self._reject_conflict_fields("missing")

        if self.fidelity is FidelityState.CONFLICT:
            if self.value is not None:
                raise ValueError("conflict claims must use candidates instead of value")
            if len(self.candidates) < 2:
                raise ValueError("conflict claims require at least two candidates")
            if not self.conflict_reason:
                raise ValueError("conflict claims require conflict_reason")

        return self

    def _reject_conflict_fields(self, fidelity_name: str) -> None:
        if self.candidates:
            raise ValueError(f"{fidelity_name} claims must not contain candidates")
        if self.conflict_reason:
            raise ValueError(f"{fidelity_name} claims must not contain conflict_reason")


class AgentTypeClaim(BaseModel):
    """Agent-type classification claim using the output-spec ``values`` field."""

    model_config = ConfigDict(extra="forbid")

    values: list[str] = Field(default_factory=list)
    fidelity: FidelityState = FidelityState.MISSING
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    rationale: str | None = None
    candidates: list[ConflictCandidate] = Field(default_factory=list)
    conflict_reason: str | None = None
    impact: str | None = None

    @model_validator(mode="after")
    def validate_fidelity_rules(self) -> AgentTypeClaim:
        """Apply claim-like fidelity rules to list-valued agent type claims."""
        if self.fidelity is FidelityState.EXPLICIT:
            if not self.values:
                raise ValueError("explicit agent_type claims require values")
            if not self.evidence_refs:
                raise ValueError("explicit agent_type claims require evidence_refs")
            self._reject_conflict_fields("explicit")

        if self.fidelity is FidelityState.INFERRED:
            if not self.values:
                raise ValueError("inferred agent_type claims require values")
            if not self.evidence_refs:
                raise ValueError("inferred agent_type claims require evidence_refs")
            if not self.rationale:
                raise ValueError("inferred agent_type claims require rationale")
            self._reject_conflict_fields("inferred")

        if self.fidelity is FidelityState.MISSING:
            if self.values:
                raise ValueError("missing agent_type claims must not contain values")
            self._reject_conflict_fields("missing")

        if self.fidelity is FidelityState.CONFLICT:
            if self.values:
                raise ValueError("conflict agent_type claims must use candidates instead of values")
            if len(self.candidates) < 2:
                raise ValueError("conflict agent_type claims require at least two candidates")
            if not self.conflict_reason:
                raise ValueError("conflict agent_type claims require conflict_reason")

        return self

    def _reject_conflict_fields(self, fidelity_name: str) -> None:
        if self.candidates:
            raise ValueError(f"{fidelity_name} agent_type claims must not contain candidates")
        if self.conflict_reason:
            raise ValueError(f"{fidelity_name} agent_type claims must not contain conflict_reason")


class SourceDocumentMetadata(BaseModel):
    """Metadata under ``source_metadata.yaml`` -> ``source``."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = "src_001"
    source_type: str = "pdf"
    file_name: str
    file_sha256: str | None = None
    page_count: int | None = Field(default=None, ge=0)
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    year: int | None = None


class ParserMetadata(BaseModel):
    """Metadata under ``source_metadata.yaml`` -> ``parser``."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    version: str | None = None
    parsed_at: str | None = None


class SourceMetadata(BaseModel):
    """Metadata about the source article and parse process."""

    model_config = ConfigDict(extra="forbid")

    source: SourceDocumentMetadata
    parser: ParserMetadata = Field(default_factory=ParserMetadata)


class GeneratorMetadata(BaseModel):
    """Generator metadata for package manifests."""

    model_config = ConfigDict(extra="forbid")

    name: str = "article2agentspec"
    version: str = SCHEMA_VERSION


class ValidationStatus(BaseModel):
    """Validation status summary for package manifests."""

    model_config = ConfigDict(extra="forbid")

    status: str = "not_run"
    warnings: list[str] = Field(default_factory=list)


class Manifest(BaseModel):
    """Package-level metadata and validation status."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION
    generator: GeneratorMetadata = Field(default_factory=GeneratorMetadata)
    source_file: str
    generated_at: str | None = None
    files: list[str] = Field(default_factory=list)
    validation: ValidationStatus = Field(default_factory=ValidationStatus)


class AgentSpecSource(BaseModel):
    """Source block in ``agent_spec.yaml``."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    source_file: str


class ModuleEntry(BaseModel):
    """Basic typed module entry for ``agent_spec.yaml``."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    role: Claim = Field(default_factory=Claim)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)


class AgentDesign(BaseModel):
    """Nested agent design block in ``agent_spec.yaml``."""

    model_config = ConfigDict(extra="forbid")

    name: Claim = Field(default_factory=Claim)
    purpose: Claim = Field(default_factory=Claim)
    agent_type: AgentTypeClaim = Field(default_factory=AgentTypeClaim)
    architecture_summary: Claim = Field(default_factory=Claim)
    modules: list[ModuleEntry] = Field(default_factory=list)
    memory: Claim = Field(default_factory=Claim)
    planning: Claim = Field(default_factory=Claim)
    tool_use: Claim = Field(default_factory=Claim)
    human_in_the_loop: Claim = Field(default_factory=Claim)
    runtime_requirements: Claim = Field(default_factory=Claim)


class AgentSpec(BaseModel):
    """Primary machine-readable agent design specification."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION
    source: AgentSpecSource
    agent: AgentDesign = Field(default_factory=AgentDesign)


class WorkflowNode(BaseModel):
    """Basic typed workflow graph node."""

    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    type: str = "unknown"
    description: Claim = Field(default_factory=Claim)


class WorkflowEdge(BaseModel):
    """Basic typed workflow graph edge."""

    model_config = ConfigDict(extra="forbid")

    id: str
    source: str
    target: str
    condition: Claim = Field(default_factory=Claim)


class WorkflowGraph(BaseModel):
    """Generic nodes + edges workflow graph."""

    model_config = ConfigDict(extra="forbid")

    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)


class WorkflowSpec(BaseModel):
    """Graph representation of the extracted agent workflow."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION
    graph: WorkflowGraph = Field(default_factory=WorkflowGraph)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class ToolEntry(BaseModel):
    """Basic typed tool inventory entry."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: Claim = Field(default_factory=Claim)
    input_schema: Claim = Field(default_factory=Claim)
    output_schema: Claim = Field(default_factory=Claim)


class ToolsSpec(BaseModel):
    """Structured tool inventory."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION
    tools: list[ToolEntry] = Field(default_factory=list)


class EvalEntry(BaseModel):
    """Basic typed evaluation entry."""

    model_config = ConfigDict(extra="forbid")

    id: str
    task: Claim = Field(default_factory=Claim)
    dataset: Claim = Field(default_factory=Claim)
    metrics: list[Claim] = Field(default_factory=list)
    baselines: list[Claim] = Field(default_factory=list)
    runtime: Claim = Field(default_factory=Claim)


class EvalConfig(BaseModel):
    """Structured evaluation configuration extracted from the source."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION
    evaluations: list[EvalEntry] = Field(default_factory=list)


__all__ = [
    "AgentDesign",
    "AgentSpec",
    "AgentSpecSource",
    "AgentTypeClaim",
    "Claim",
    "ConflictCandidate",
    "EvalConfig",
    "EvalEntry",
    "EvidenceRef",
    "FidelityState",
    "Manifest",
    "ModuleEntry",
    "SourceMetadata",
    "ToolEntry",
    "ToolsSpec",
    "WorkflowEdge",
    "WorkflowNode",
    "WorkflowSpec",
]
