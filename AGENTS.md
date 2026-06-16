# AGENTS.md

This file provides working instructions for humans, Codex, Claude, and other
coding agents contributing to Article2AgentSpec.

Article2AgentSpec is a CLI-first Python tool that converts PDF articles about
LLM-based agent architectures into evidence-grounded agent design packages.

## Read This First

Before changing implementation code, read these documents in order:

1. `docs/fidelity-policy.md`
2. `docs/output-spec.md`
3. `docs/project-spec.md`
4. `README.md`

The fidelity policy is the highest-priority project rule. If implementation
convenience conflicts with source fidelity, source fidelity wins.

## Core Contract

The conversion pipeline is:

```text
parse -> extract -> validate -> write
```

Do not bypass validation before writing normal output packages.

The default output location is:

```text
outputs/<source_stem>/
```

The required MVP output files are:

```text
manifest.yaml
source_metadata.yaml
source_text.md
agent_spec.yaml
workflow.json
tools.json
eval_config.yaml
prompts.md
implementation_notes.md
evidence_report.md
```

## Fidelity Rules

Use these states for extracted claims:

- `explicit`: directly stated by the source article
- `inferred`: architecture-level interpretation grounded in source evidence
- `missing`: not provided by the source article
- `conflict`: incompatible source claims preserved as candidates

Rules:

- Do not invent concrete configuration values.
- Do not infer prompts, model versions, temperatures, thresholds, retry limits,
  dataset splits, or tool schemas.
- Architecture-level inference is allowed only when marked `inferred`, supported
  by evidence, and accompanied by rationale.
- Every non-empty `explicit`, `inferred`, or `conflict` claim must have
  `evidence_refs`.
- Structured files should contain compact evidence IDs only. Long excerpts
  belong in `evidence_report.md`.

## MVP Scope

Implement the MVP first:

- local PDF input
- Markdown, YAML, and JSON output
- command names `article2agentspec` and `a2as`
- Pydantic models for structured outputs
- JSON Schema export
- validation before write
- no required external LLM API calls

Do not add arXiv search, web ingestion, a web app, MCP server mode, or code
generation until the MVP contract is implemented.

## External LLM Policy

The default path must run locally without API keys.

Optional LLM-assisted extraction may be added only behind explicit user
configuration. LLM output must still be treated as extracted or inferred content,
not as source truth. LLM guesses must never be marked `explicit`.

## Expected Repository Shape

Recommended implementation layout:

```text
pyproject.toml
article2agentspec/
  __init__.py
  __main__.py
  cli.py
  pipeline.py
  parsing/
  extraction/
  validation/
  writing/
tests/
docs/
schemas/
  article2agentspec/
    models.py
    export_json_schema.py
    json_schema/
```

The top-level `schemas/article2agentspec/` directory contains the canonical
Pydantic models and JSON Schema exports. Do not define parallel schema shapes in
implementation code.

## Development Guidelines

- Keep changes scoped to the requested task.
- Prefer simple, explicit Python over premature abstraction.
- Use typed Pydantic models for package data structures.
- Keep deterministic extraction independent from optional LLM extraction.
- Preserve page numbers and source locators during parsing.
- Make validation errors specific and actionable.
- Do not write output files from partially validated data.
- Do not commit generated debug artifacts unless explicitly requested.

## Code Standards

Use the lightweight project standard:

- Use `ruff` for formatting and linting.
- Use `pytest` for tests.
- Do not enable `mypy` yet.
- Keep type annotations on public functions, public methods, schema boundaries,
  and pipeline boundaries.
- Prefer precise domain models over unbounded `dict[str, Any]` at module
  boundaries.
- Keep `cli.py` thin. It should parse arguments, call the pipeline, and format
  user-facing errors.
- Keep `pipeline.py` focused on orchestration. It should not parse PDFs, extract
  claims, validate schemas, or write files directly.
- Keep `parsing` responsible for source reading and locators only.
- Keep `extraction` responsible for draft structured claims only.
- Keep `validation` responsible for schema, fidelity, and evidence checks only.
- Keep `writing` responsible for writing already-validated packages only.
- Library code should not call `print`; reserve console output for the CLI
  layer.
- Do not introduce runtime dependencies without a clear MVP need.
- Prefer deterministic behavior by default. Optional LLM behavior must remain
  explicit and isolated.

## Testing Guidelines

Tests should cover:

- CLI command parsing
- PDF parsing fixtures
- source metadata generation
- fidelity validation
- evidence reference resolution
- package writer behavior
- JSON Schema export

Default tests must not require external LLM API keys.

Use focused pytest tests for each module boundary. Prefer small fixtures and
deterministic inputs over broad integration tests while the MVP is being built.

When the project has a test runner configured, run the relevant tests before
claiming implementation work is complete.

## Output Review Checklist

Before considering a generated package valid, check that:

- all required files exist
- YAML and JSON files parse successfully
- structured outputs conform to Pydantic models
- evidence references resolve
- non-empty design claims have evidence
- missing fields are not silently omitted when they affect reproducibility
- conflicts are preserved as candidates
- implementation notes identify gaps, uncertainty, conflicts, and human
  confirmation needs

## Documentation Update Rule

If a change alters package structure, fidelity behavior, CLI behavior, or schema
fields, update the relevant docs in the same change:

- `docs/fidelity-policy.md`
- `docs/output-spec.md`
- `docs/project-spec.md`
- `README.md`

Do not let implementation behavior drift away from the documented contract.
