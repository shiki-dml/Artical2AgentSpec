# Output Specification

Article2AgentSpec converts a source article into an `agent_package`: a directory
containing human-readable Markdown and machine-readable YAML/JSON files that
describe the agent architecture implied by the article.

The output must be readable by humans and actionable for coding agents, while
remaining faithful to the source article.

## Default Output Location

By default, the CLI writes packages to:

```text
outputs/<source_stem>/
```

For example:

```bash
article2agentspec convert downloads/paper.pdf
```

produces:

```text
outputs/paper/
```

The user may override the output root:

```bash
article2agentspec convert downloads/paper.pdf -o custom-output/
a2as convert downloads/paper.pdf -o custom-output/
```

## Package Structure

The MVP package structure is:

```text
outputs/<source_stem>/
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

When `--debug` is enabled, the package may also include:

```text
outputs/<source_stem>/
  debug/
    raw_pdf_parse.json
    chunks.json
    extraction_trace.json
    validation_report.json
```

Debug files are not part of the stable package contract.

## File Responsibilities

### manifest.yaml

Package-level metadata and validation status.

Required content:

- package schema version
- generator name and version
- source file reference
- generation timestamp
- list of generated files
- validation status
- warnings summary

Example:

```yaml
schema_version: "0.1.0"
generator:
  name: "article2agentspec"
  version: "0.1.0"
source_file: "paper.pdf"
generated_at: "2026-06-16T00:00:00Z"
files:
  - agent_spec.yaml
  - workflow.json
  - tools.json
  - eval_config.yaml
  - prompts.md
  - implementation_notes.md
  - evidence_report.md
validation:
  status: "passed"
  warnings: []
```

### source_metadata.yaml

Metadata about the source document and parsing process.

Recommended fields:

```yaml
source:
  source_id: "src_001"
  source_type: "pdf"
  file_name: "paper.pdf"
  file_sha256: null
  page_count: null
  title: null
  authors: []
  year: null
parser:
  name: null
  version: null
  parsed_at: null
```

### source_text.md

Lightweight parsed text for inspection and evidence traceability.

For PDF input, the file should preserve page boundaries:

```markdown
# Source Text

## Page 1

...

## Page 2

...
```

This file is intended for debugging and review, not as the primary structured
output.

### agent_spec.yaml

The primary machine-readable agent design specification.

It describes the article's implied agent, including:

- agent identity and purpose
- supported agent type classifications
- architecture summary
- modules
- memory
- planning
- tool use
- RAG behavior
- multi-agent behavior
- runtime requirements
- implementation constraints

Each non-empty design claim must include `fidelity` and `evidence_refs`.

Minimal shape:

```yaml
schema_version: "0.1.0"
source:
  title: null
  authors: []
  year: null
  source_file: "paper.pdf"
agent:
  name:
    value: null
    fidelity: missing
    evidence_refs: []
  purpose:
    value: null
    fidelity: missing
    evidence_refs: []
  agent_type:
    values: []
    fidelity: missing
    evidence_refs: []
  architecture_summary:
    value: null
    fidelity: missing
    evidence_refs: []
  modules: []
  memory:
    value: null
    fidelity: missing
    evidence_refs: []
  planning:
    value: null
    fidelity: missing
    evidence_refs: []
  tool_use:
    value: null
    fidelity: missing
    evidence_refs: []
  human_in_the_loop:
    value: null
    fidelity: missing
    evidence_refs: []
  runtime_requirements:
    value: null
    fidelity: missing
    evidence_refs: []
```

Allowed `agent_type.values`:

- `llm_based`
- `tool_use`
- `workflow`
- `multi_agent`
- `rag`
- `browser`
- `coding`

Module entries should use this shape:

```yaml
- id: "retriever"
  name: "Retriever"
  role:
    value: "Retrieves external context before answer generation."
    fidelity: explicit
    evidence_refs:
      - ev_012
  inputs: []
  outputs: []
  dependencies: []
```

### workflow.json

Graph representation of the agent workflow.

The workflow uses a generic `nodes + edges` model.

Required top-level shape:

```json
{
  "schema_version": "0.1.0",
  "graph": {
    "nodes": [],
    "edges": []
  },
  "evidence_refs": []
}
```

Node shape:

```json
{
  "id": "retrieve_context",
  "label": "Retrieve context",
  "type": "retrieval",
  "description": {
    "value": "Retrieve relevant documents before generation.",
    "fidelity": "explicit",
    "evidence_refs": ["ev_012"]
  }
}
```

Edge shape:

```json
{
  "id": "edge_retrieve_to_generate",
  "source": "retrieve_context",
  "target": "generate_answer",
  "condition": {
    "value": null,
    "fidelity": "missing",
    "evidence_refs": []
  }
}
```

Recommended node types:

- `input`
- `llm_call`
- `planning`
- `retrieval`
- `tool_call`
- `browser_action`
- `code_action`
- `memory_read`
- `memory_write`
- `routing`
- `aggregation`
- `evaluation`
- `output`
- `unknown`

### tools.json

Structured tool inventory and tool schemas.

If the article describes a tool but does not provide an input schema, the tool
should be present with schema fields marked `missing`.

Shape:

```json
{
  "schema_version": "0.1.0",
  "tools": [
    {
      "id": "web_search",
      "name": "Web Search",
      "description": {
        "value": "Searches the web for external information.",
        "fidelity": "explicit",
        "evidence_refs": ["ev_020"]
      },
      "input_schema": {
        "value": null,
        "fidelity": "missing",
        "evidence_refs": []
      },
      "output_schema": {
        "value": null,
        "fidelity": "missing",
        "evidence_refs": []
      }
    }
  ]
}
```

### eval_config.yaml

Structured description of experiments, tasks, datasets, metrics, baselines, and
runtime settings described in the source.

Example:

```yaml
schema_version: "0.1.0"
evaluations:
  - id: "main_eval"
    task:
      value: null
      fidelity: missing
      evidence_refs: []
    dataset:
      value: null
      fidelity: missing
      evidence_refs: []
    metrics: []
    baselines: []
    runtime:
      value: null
      fidelity: missing
      evidence_refs: []
```

Concrete values such as model version, temperature, dataset split, or number of
runs must not be inferred.

### prompts.md

Human-readable prompt inventory.

Only prompts explicitly provided by the source should be included as prompt
text. If the article describes prompt behavior but does not provide the text,
record the prompt as missing.

Suggested structure:

````markdown
# Prompts

## prompt_001: Planner Prompt

Status: explicit
Evidence: ev_030

```text
...
```

## Missing Prompts

- The source describes a generation prompt but does not provide the text.
````

### implementation_notes.md

Human-readable implementation guidance and reproducibility gaps.

This file must list:

- missing information
- unresolved conflicts
- inferred architecture decisions
- uncertainty
- implementation risks
- items requiring human confirmation
- reproducibility blockers

It should not invent missing details.

### evidence_report.md

Human-readable evidence report.

This file expands compact evidence IDs into source references, short excerpts,
and explanations.

Suggested structure:

```markdown
# Evidence Report

## Evidence Index

### ev_001

- Source: src_001
- Page: 3
- Locator: paragraph 2
- Supports: agent purpose
- Excerpt: "..."

## Claim Coverage

- agent.purpose: ev_001
- workflow.nodes.retrieve_context: ev_012
```

Long quotations should be avoided unless necessary. Evidence excerpts should be
short and focused.

## Evidence References

All structured evidence references use stable IDs:

```text
ev_001
ev_002
ev_003
```

An evidence reference must resolve to an entry in `evidence_report.md` or a
future structured evidence index.

PDF evidence should include page numbers. Markdown and HTML evidence, when
supported, should include section and line numbers.

## Validation Contract

The CLI must execute:

```text
parse -> extract -> validate -> write
```

The write step must only run after successful validation.

Validation must check:

- required files are present
- YAML and JSON files parse successfully
- structured outputs conform to Pydantic models
- JSON Schema exports are available for machine consumers
- evidence IDs referenced in structured files exist
- non-empty `explicit`, `inferred`, and `conflict` claims have evidence
- `inferred` claims include rationales
- `missing` claims do not contain invented values
- conflicts preserve multiple candidates

## Schema Location

Runtime Pydantic models should live under:

```text
schemas/article2agentspec/
```

JSON Schema exports should live under:

```text
schemas/article2agentspec/json_schema/
```

The exact Python package layout may evolve, but schema definitions are part of
the project contract and must remain versioned.
