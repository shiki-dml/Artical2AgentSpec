# Article2AgentSpec

Article2AgentSpec is a CLI-first Python project for converting articles about
LLM-based agent architectures into evidence-grounded agent design packages.

The target input for the MVP is a local PDF file. The target output is an
`agent_package` directory containing human-readable Markdown and
machine-readable YAML/JSON files.

> Status: package skeleton stage. The project contract is defined, and the
> installable Python package skeleton exists. Conversion logic has not been
> implemented yet.

## What It Produces

For a source PDF, Article2AgentSpec produces:

- a readable agent design summary
- a structured `agent_spec.yaml`
- a graph-based `workflow.json`
- a `tools.json` inventory with schemas when available
- an `eval_config.yaml` file for experiment settings
- a `prompts.md` file for explicitly provided prompts
- an `implementation_notes.md` file for gaps, conflicts, uncertainty, and
  reproduction notes
- an `evidence_report.md` file linking claims back to the source

Default output location:

```text
outputs/<source_stem>/
```

Example package:

```text
outputs/paper/
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

## Planned CLI

The package currently exposes placeholder console scripts so installation can be
verified before conversion logic is added.

Primary command:

```bash
article2agentspec convert path/to/paper.pdf
```

Short alias:

```bash
a2as convert path/to/paper.pdf
```

Custom output root:

```bash
article2agentspec convert path/to/paper.pdf -o outputs/
```

Debug artifacts:

```bash
article2agentspec convert path/to/paper.pdf --debug
```

The required pipeline is:

```text
parse -> extract -> validate -> write
```

Normal output must not be written before validation passes.

## Fidelity Policy

Article2AgentSpec is conservative by default.

The tool uses four fidelity states:

- `explicit`: directly stated by the article
- `inferred`: architecture-level interpretation grounded in source evidence
- `missing`: not provided by the article
- `conflict`: incompatible source claims preserved as candidates

Important constraints:

- Concrete configuration values must not be inferred.
- Missing prompts, model versions, thresholds, tool schemas, and experiment
  settings must be marked missing instead of guessed.
- Every non-empty `explicit`, `inferred`, or `conflict` claim must have evidence.
- PDF evidence should include page numbers.

See `docs/fidelity-policy.md` for the full rules.

## MVP Scope

The MVP supports:

- local PDF input
- Markdown, YAML, and JSON output
- output packages under `outputs/<source_stem>/`
- Pydantic validation
- JSON Schema exports
- no required external LLM API calls

The MVP targets articles about:

- LLM agents
- tool-use agents
- workflow agents
- multi-agent systems
- RAG agents
- browser agents
- coding agents

## Not In MVP

The first version does not need to include:

- arXiv search
- web page ingestion
- Markdown or HTML ingestion
- web UI
- MCP server mode
- automatic experiment reproduction
- full implementation code generation for the extracted agent
- mandatory external LLM API calls

## Documentation

- `docs/fidelity-policy.md`: rules for explicit, inferred, missing, and
  conflict claims
- `docs/output-spec.md`: `agent_package` structure and field expectations
- `docs/project-spec.md`: goals, MVP scope, architecture, and non-goals
- `AGENTS.md`: working instructions for developers and coding agents

## Development Notes

The implementation should remain local-first. Optional LLM-assisted extraction
may be added later, but it must be explicitly enabled and must still obey the
same validation and fidelity rules.

Expected implementation direction:

- Python CLI
- Pydantic models for structured outputs
- JSON Schema export
- deterministic baseline extraction
- optional provider abstraction for future LLM-assisted extraction

Tests should not require external API keys by default.
