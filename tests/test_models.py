from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from schemas.article2agentspec.export_json_schema import export_json_schemas
from schemas.article2agentspec.models import (
    AgentSpec,
    Claim,
    ConflictCandidate,
    EvalConfig,
    EvalEntry,
    FidelityState,
    Manifest,
    SourceMetadata,
    ToolEntry,
    ToolsSpec,
    WorkflowEdge,
    WorkflowNode,
    WorkflowSpec,
)


def test_claim_uses_string_evidence_refs_and_enforces_fidelity_rules() -> None:
    with pytest.raises(ValidationError, match="explicit claims require evidence_refs"):
        Claim(value="retrieves context", fidelity=FidelityState.EXPLICIT)

    with pytest.raises(ValidationError, match="inferred claims require rationale"):
        Claim(
            value="uses a RAG architecture",
            fidelity=FidelityState.INFERRED,
            evidence_refs=["ev_001"],
        )

    with pytest.raises(ValidationError, match="missing claims must not contain a value"):
        Claim(value="gpt-4.1", fidelity=FidelityState.MISSING)

    claim = Claim(
        value="uses a RAG architecture",
        fidelity=FidelityState.INFERRED,
        evidence_refs=["ev_001"],
        rationale="The source describes retrieval before generation.",
    )

    assert claim.evidence_refs == ["ev_001"]


def test_conflict_claim_preserves_string_evidence_refs() -> None:
    candidate_a = ConflictCandidate(value=3, evidence_refs=["ev_001"])
    candidate_b = ConflictCandidate(value=4, evidence_refs=["ev_002"], preferred=True)

    claim = Claim(
        fidelity=FidelityState.CONFLICT,
        candidates=[candidate_a, candidate_b],
        conflict_reason="The method text and figure describe different agent counts.",
    )

    assert claim.candidates[1].evidence_refs == ["ev_002"]
    assert claim.candidates[1].preferred is True

    with pytest.raises(ValidationError, match="conflict claims require at least two candidates"):
        Claim(
            fidelity=FidelityState.CONFLICT,
            candidates=[candidate_a],
            conflict_reason="Only one candidate is not a conflict.",
        )


def test_source_metadata_matches_output_spec_nesting() -> None:
    metadata = SourceMetadata(
        source={
            "source_id": "src_001",
            "source_type": "pdf",
            "file_name": "paper.pdf",
            "page_count": 12,
        },
        parser={"name": "pypdf", "version": "1.0.0", "parsed_at": "2026-06-16T00:00:00Z"},
    )

    assert metadata.source.file_name == "paper.pdf"
    assert metadata.source.source_type == "pdf"
    assert metadata.parser.name == "pypdf"


def test_agent_spec_uses_source_and_agent_nesting() -> None:
    agent_spec = AgentSpec(
        source={"source_file": "paper.pdf", "title": "Agent Paper", "authors": ["A. Author"]},
        agent={
            "purpose": {
                "value": "Answer questions with retrieved context.",
                "fidelity": "explicit",
                "evidence_refs": ["ev_001"],
            },
            "agent_type": {
                "values": ["rag", "tool_use"],
                "fidelity": "inferred",
                "evidence_refs": ["ev_002"],
                "rationale": "The source describes retrieval and tool calls.",
            },
            "modules": [
                {
                    "id": "retriever",
                    "name": "Retriever",
                    "role": {
                        "value": "Retrieves context.",
                        "fidelity": "explicit",
                        "evidence_refs": ["ev_003"],
                    },
                }
            ],
        },
    )

    assert agent_spec.source.source_file == "paper.pdf"
    assert agent_spec.agent.purpose.evidence_refs == ["ev_001"]
    assert agent_spec.agent.agent_type.values == ["rag", "tool_use"]
    assert agent_spec.agent.modules[0].role.value == "Retrieves context."


def test_workflow_tools_and_eval_use_typed_entries() -> None:
    workflow = WorkflowSpec(
        graph={
            "nodes": [
                WorkflowNode(
                    id="retrieve_context",
                    label="Retrieve context",
                    type="retrieval",
                    description=Claim(
                        value="Retrieve relevant documents before generation.",
                        fidelity=FidelityState.EXPLICIT,
                        evidence_refs=["ev_010"],
                    ),
                )
            ],
            "edges": [
                WorkflowEdge(
                    id="edge_retrieve_to_generate",
                    source="retrieve_context",
                    target="generate_answer",
                )
            ],
        },
        evidence_refs=["ev_010"],
    )
    tools = ToolsSpec(
        tools=[
            ToolEntry(
                id="web_search",
                name="Web Search",
                description=Claim(
                    value="Searches the web.",
                    fidelity=FidelityState.EXPLICIT,
                    evidence_refs=["ev_020"],
                ),
            )
        ]
    )
    eval_config = EvalConfig(
        evaluations=[
            EvalEntry(
                id="main_eval",
                task=Claim(
                    value="Question answering.",
                    fidelity=FidelityState.EXPLICIT,
                    evidence_refs=["ev_030"],
                ),
            )
        ]
    )

    assert workflow.graph.nodes[0].id == "retrieve_context"
    assert workflow.graph.edges[0].target == "generate_answer"
    assert tools.tools[0].input_schema.fidelity is FidelityState.MISSING
    assert eval_config.evaluations[0].dataset.fidelity is FidelityState.MISSING


def test_manifest_accepts_minimal_mvp_shape() -> None:
    manifest = Manifest(source_file="paper.pdf", files=["agent_spec.yaml"])

    assert manifest.generator.name == "article2agentspec"
    assert manifest.validation.status == "not_run"


def test_export_json_schemas_writes_required_schema_files(tmp_path) -> None:
    written = export_json_schemas(tmp_path)

    expected_files = {
        "source_metadata.schema.json",
        "agent_spec.schema.json",
        "workflow.schema.json",
        "tools.schema.json",
        "eval_config.schema.json",
        "manifest.schema.json",
    }

    assert {path.name for path in written} == expected_files

    for file_name in expected_files:
        schema_path = tmp_path / file_name
        assert schema_path.exists()
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        assert schema["type"] == "object"
