"""Deterministic baseline extraction for the no-LLM MVP path."""

from __future__ import annotations

from article2agentspec.extraction.base import PackageDraft
from article2agentspec.parsing.pdf import ParsedDocument
from schemas.article2agentspec.models import AgentSpec, AgentSpecSource, EvalConfig, ToolsSpec, WorkflowSpec


def extract_baseline(parsed: ParsedDocument) -> PackageDraft:
    """Create a conservative package draft from parsed PDF text."""
    source_metadata = parsed.to_source_metadata()
    return PackageDraft(
        source_stem=parsed.source_stem,
        source_metadata=source_metadata,
        source_text_md=_render_source_text(parsed),
        agent_spec=AgentSpec(
            source=AgentSpecSource(
                title=source_metadata.source.title,
                authors=source_metadata.source.authors,
                year=source_metadata.source.year,
                source_file=parsed.file_name,
            )
        ),
        workflow=WorkflowSpec(),
        tools=ToolsSpec(),
        eval_config=EvalConfig(),
        prompts_md=_render_prompts(),
        implementation_notes_md=_render_implementation_notes(parsed),
        evidence_report_md=_render_evidence_report(),
        evidence_ids=set(),
        debug_artifacts={
            "raw_pdf_parse.json": parsed.to_debug_dict(),
        },
    )


def _render_source_text(parsed: ParsedDocument) -> str:
    sections = ["# Source Text", ""]
    for page in parsed.pages:
        sections.extend(
            [
                f"## Page {page.page_number}",
                "",
                page.text.strip(),
                "",
            ]
        )
    return "\n".join(sections).rstrip() + "\n"


def _render_prompts() -> str:
    return (
        "# Prompts\n\n"
        "## Missing Prompts\n\n"
        "- Baseline extraction did not identify explicitly provided prompt text.\n"
    )


def _render_implementation_notes(parsed: ParsedDocument) -> str:
    return (
        "# Implementation Notes\n\n"
        "## Baseline extraction\n\n"
        "- This MVP run used deterministic baseline extraction without an external LLM.\n"
        "- Agent design fields are marked missing unless supported by explicit extraction.\n"
        "- Workflow, tool, evaluation, and prompt details require human review or richer extraction.\n\n"
        "## Source coverage\n\n"
        f"- Parsed {parsed.page_count} PDF page(s) from `{parsed.file_name}`.\n"
    )


def _render_evidence_report() -> str:
    return (
        "# Evidence Report\n\n"
        "## Evidence Index\n\n"
        "No explicit design claims were extracted by the baseline extractor.\n\n"
        "## Claim Coverage\n\n"
        "All design claims are marked missing in the baseline package.\n"
    )
