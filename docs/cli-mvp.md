# CLI MVP

This document fixes the minimum CLI scope for the first runnable
Article2AgentSpec conversion path.

## Command

Supported commands:

```bash
article2agentspec convert paper.pdf -o outputs --debug
a2as convert paper.pdf -o outputs --debug
```

Arguments:

- `convert`: the only MVP subcommand.
- `source_pdf`: required local PDF path.
- `-o, --output-root`: optional output root. Defaults to `outputs`.
- `--debug`: optional flag that writes debug artifacts.
- `-h, --help`: standard argparse help.

The MVP CLI does not include schema export, package validation, arXiv, web
ingestion, Markdown ingestion, LLM configuration, or code generation commands.

## Exit Codes

- `0`: conversion succeeded and the agent package was written.
- `1`: runtime failure, including missing input, non-PDF input, parse failure,
  validation failure, or write failure.
- `2`: command-line usage error from argparse.

On success, the CLI prints the package directory:

```text
Wrote agent package: outputs/paper
```

On runtime failure, the CLI prints a concise error to stderr:

```text
error: input file does not exist: missing.pdf
```

Library code must not print directly.

## Pipeline Boundary

The CLI must call the pipeline, and the pipeline must run:

```text
parse -> extract -> validate -> write
```

Normal output files must not be written unless validation succeeds.

## Component Responsibilities

- `exceptions.py`: project-specific exception types for CLI-facing failures.
- `parsing/pdf.py`: validate local PDF input, compute file metadata, extract
  text by page, and preserve page numbers.
- `extraction/heuristic.py`: create a deterministic baseline package draft
  without external LLM calls. Most design fields are marked `missing`.
- `validation/validators.py`: validate canonical Pydantic models and evidence
  references before writing.
- `writing/package_writer.py`: write already validated package data to the 10
  required MVP output files, with optional debug artifacts.
- `pipeline.py`: orchestrate parse, extract, validate, and write.
- `cli.py`: parse arguments, call the pipeline, and format user-facing errors.

## Baseline Extraction

The MVP extractor is conservative:

- It reads PDF text and writes `source_text.md`.
- It fills source metadata from local file and parser information.
- It does not infer concrete model names, parameters, prompts, thresholds,
  retry limits, dataset splits, or tool schemas.
- It does not call external LLM APIs.
- It emits empty workflow, tool, and eval structures when unsupported by
  explicit extraction.
- It records missing implementation details in `implementation_notes.md`.

## Output Files

Every successful conversion writes:

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

When `--debug` is set, the writer may also write:

```text
debug/raw_pdf_parse.json
debug/validation_report.json
```

## Dependencies

Runtime dependencies:

```toml
dependencies = [
  "pydantic>=2",
  "pypdf>=5",
  "PyYAML>=6",
]
```

Development dependencies:

```toml
[project.optional-dependencies]
dev = [
  "pytest>=8",
  "ruff>=0.6",
]
```

## Tests

Focused tests should cover:

- CLI help, missing input, non-PDF input, and successful conversion.
- PDF parsing metadata, page count, text extraction, and sha256.
- Validation success for missing-heavy baseline packages.
- Validation failure for unresolved evidence references.
- Writer creation of all 10 required MVP files.
- End-to-end conversion from a small PDF fixture.
