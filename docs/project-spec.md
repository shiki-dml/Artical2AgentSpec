# Project Specification

Article2AgentSpec is a CLI-first Python tool that converts articles describing
LLM-based agent architectures into structured agent design packages.

The project serves two related documentation layers:

1. Project implementation guidance for human developers and coding agents.
2. Output specifications that describe the agent implied by a source article.

The first layer explains how this tool should be built and maintained. The
second layer defines how the tool represents an article's implied agent so that
humans can understand it and agents can help reproduce it.

## Goals

Article2AgentSpec should help users turn an agent architecture article into:

- a readable summary of the implied agent design
- a structured specification suitable for agent developers and coding agents
- a graph representation of the workflow
- a tool inventory with schemas when available
- extracted prompts when explicitly provided
- evaluation configuration when described by the source
- an evidence report linking claims back to the source article
- implementation notes identifying missing, conflicting, or uncertain details

The tool must preserve source fidelity. It should make missing information
visible instead of inventing it.

## Primary Users

### Human agent developers

Human readers should be able to inspect the generated Markdown files and quickly
understand:

- what agent the article describes
- what modules and workflows are involved
- which details are explicit, inferred, missing, or conflicting
- what would be required to reproduce the agent

### Coding agents

Coding agents should be able to read the project docs and generated YAML/JSON
files to:

- understand the expected package structure
- follow implementation constraints
- validate structured outputs
- use evidence references when making implementation decisions

## MVP Scope

The first version supports:

- local PDF input
- Markdown, YAML, and JSON output
- package output under `outputs/<source_stem>/`
- conservative extraction
- explicit fidelity states
- PDF page-level evidence references
- Pydantic validation before writing
- JSON Schema exports for structured output formats
- command aliases: `article2agentspec` and `a2as`

The MVP conversion command is:

```bash
article2agentspec convert path/to/paper.pdf
a2as convert path/to/paper.pdf
```

Optional output root:

```bash
article2agentspec convert path/to/paper.pdf -o outputs/
```

Debug output:

```bash
article2agentspec convert path/to/paper.pdf --debug
```

## Non-Goals For MVP

The first version does not need to support:

- automatic arXiv search
- web page ingestion
- Markdown or HTML ingestion
- full code generation for the extracted agent
- automatic reproduction of experiments
- visual rendering of workflow diagrams
- mandatory external LLM API calls
- a web application
- an MCP server
- package publishing

These may be added later, but they should not complicate the MVP design.

## Supported Agent Article Types

The MVP targets articles about LLM-based systems, including:

- LLM agents
- tool-use agents
- workflow agents
- multi-agent systems
- RAG agents
- browser agents
- coding agents

The MVP does not target non-LLM robotics systems, symbolic-only planners, or
general software architecture articles unless they are directly framed as
LLM-based agent systems.

## Core Pipeline

The CLI pipeline is:

```text
parse -> extract -> validate -> write
```

### parse

Input:

- local PDF file

Output:

- source metadata
- lightweight parsed text
- page boundaries
- optional debug parse artifacts

Responsibilities:

- read the PDF
- extract text in page order
- preserve source locators for evidence
- compute basic file metadata

### extract

Input:

- parsed source text

Output:

- draft `agent_spec`
- draft workflow graph
- draft tool inventory
- draft evaluation config
- prompt inventory
- evidence entries
- implementation notes

Responsibilities:

- identify explicit article claims
- classify allowed architecture-level inferences
- mark missing and conflicting information
- attach evidence references to non-empty claims

The default extractor must not require an external LLM API. Optional LLM-backed
extractors may be added behind explicit configuration.

### validate

Input:

- extracted package model

Output:

- validation result
- validation warnings or errors

Responsibilities:

- parse all structured outputs into Pydantic models
- enforce the fidelity policy
- ensure evidence references resolve
- ensure conflicts preserve candidates
- ensure missing values are not invented
- export or verify JSON Schema compatibility

The CLI must not write a normal package if validation fails.

### write

Input:

- validated package model

Output:

- `outputs/<source_stem>/` package

Responsibilities:

- write YAML, JSON, and Markdown files
- write lightweight intermediate artifacts
- write debug artifacts only when `--debug` is enabled
- produce a manifest with validation status

## Architecture

Recommended package layout:

```text
article2agentspec/
  __init__.py
  cli.py
  pipeline.py
  parsing/
    __init__.py
    pdf.py
  extraction/
    __init__.py
    base.py
    heuristic.py
    llm_optional.py
  validation/
    __init__.py
    validators.py
  writing/
    __init__.py
    package_writer.py
tests/
docs/
schemas/
  article2agentspec/
    models.py
    export_json_schema.py
    json_schema/
```

The top-level `schemas/article2agentspec/` directory contains the canonical
Pydantic models and JSON Schema exports. Runtime code should import or reuse
these canonical models rather than defining parallel schema shapes.

## External LLM Policy

External LLM APIs are optional enhancements.

Default behavior:

- does not require API keys
- does not call external LLM providers
- produces conservative output from local parsing and deterministic extraction
  where possible

Optional behavior:

- may use an LLM to improve extraction quality
- must be explicitly enabled by the user
- must still obey the fidelity policy
- must still validate before writing
- must not treat LLM guesses as explicit source claims

Provider abstraction should be introduced only when needed. The MVP may define
interfaces without fully implementing every provider.

## Output Package Contract

The generated package is documented in `docs/output-spec.md`.

The required MVP files are:

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

The package should be useful even when many fields are marked `missing`.

## Fidelity Contract

The fidelity rules are documented in `docs/fidelity-policy.md`.

Short version:

- `explicit`: directly stated by the article
- `inferred`: architecture-level interpretation supported by evidence
- `missing`: not provided by the article
- `conflict`: incompatible source claims are preserved as candidates

Concrete configuration values must not be inferred.

## Error Handling

The CLI should fail clearly when:

- the input file does not exist
- the input file is not a PDF in the MVP
- the PDF cannot be parsed
- validation fails
- the output directory cannot be written

Validation errors should identify:

- file or model path
- failed rule
- offending field
- suggested remediation when possible

## Testing Expectations

The project should include tests for:

- CLI argument parsing
- PDF parsing behavior on small fixtures
- source metadata generation
- fidelity validation rules
- evidence reference resolution
- package writing
- JSON Schema export
- deterministic behavior for non-LLM extraction

Tests must not require external LLM API keys by default.

## Extension Roadmap

Likely future extensions:

- arXiv lookup and download
- Markdown and HTML ingestion
- richer PDF layout handling
- optional LLM-assisted extraction
- workflow diagram rendering
- agent implementation scaffolding
- MCP server mode
- web UI
- benchmark harness for extraction quality

Each extension should preserve the same core pipeline:

```text
parse -> extract -> validate -> write
```
