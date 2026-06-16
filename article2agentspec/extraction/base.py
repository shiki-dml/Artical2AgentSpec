"""Extraction data structures shared by deterministic and optional extractors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from schemas.article2agentspec.models import AgentSpec, EvalConfig, SourceMetadata, ToolsSpec, WorkflowSpec


@dataclass
class PackageDraft:
    """Complete draft package data produced before validation and writing."""

    source_stem: str
    source_metadata: SourceMetadata
    source_text_md: str
    agent_spec: AgentSpec
    workflow: WorkflowSpec
    tools: ToolsSpec
    eval_config: EvalConfig
    prompts_md: str
    implementation_notes_md: str
    evidence_report_md: str
    evidence_ids: set[str] = field(default_factory=set)
    debug_artifacts: dict[str, Any] = field(default_factory=dict)
