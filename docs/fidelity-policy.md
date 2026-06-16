# Fidelity Policy

This document defines how Article2AgentSpec represents claims extracted from a
source article. The goal is to preserve fidelity to the article while still
making the implied agent architecture understandable and reproducible.

The default policy is conservative extraction:

- Do not invent concrete configuration values.
- Do not fill missing prompts, model names, thresholds, tool parameters, or
  experiment settings unless the source explicitly provides them.
- Architecture-level inference is allowed only when it is grounded in source
  evidence and marked as inferred.
- Every non-empty design claim must be traceable to evidence.

## Fidelity States

Every extracted design claim uses one of four fidelity states.

### explicit

Use `explicit` when the source directly states the claim.

Examples:

- The article names a retrieval module.
- The article says the agent calls a browser tool.
- The article provides a prompt template.
- The article reports an evaluation dataset.

Requirements:

- The claim must include one or more `evidence_refs`.
- The evidence must support the claim without requiring architectural
  interpretation.

### inferred

Use `inferred` when the claim is an architecture-level interpretation grounded
in explicit evidence, but not directly stated as a formal design element.

Allowed inferred claims include:

- Identifying a planning stage from a described sequence of reasoning and tool
  calls.
- Classifying the system as a RAG agent when the article describes retrieval
  over external documents before generation.
- Classifying a set of cooperating LLM components as a multi-agent workflow
  when the article describes role-specialized LLM workers.

Disallowed inferred claims include:

- Specific model versions not named by the article.
- Temperature, top-p, retry limits, timeout values, or other runtime settings
  not provided by the source.
- Tool schemas not present in the article.
- Prompt text that is merely guessed from behavior.

Requirements:

- The claim must include one or more `evidence_refs`.
- The claim must include a short rationale explaining the inference.
- The claim must not introduce unsupported concrete configuration values.

### missing

Use `missing` when the source does not provide enough information to populate a
field.

Examples:

- The article describes a tool but does not provide its input schema.
- The article evaluates an agent but does not name the model version.
- The article describes an interaction loop but does not provide prompts.

Requirements:

- `missing` fields may omit `evidence_refs`.
- The output should explain the impact of the missing information when it
  affects implementation or reproducibility.

### conflict

Use `conflict` when two or more source passages appear to make incompatible
claims.

Examples:

- One section describes three agents, while another describes four.
- A figure shows a retrieval step, but the method text says no external memory
  is used.
- An experiment table names one benchmark, while the appendix names a different
  benchmark for the same result.

Requirements:

- Preserve the competing candidates instead of overwriting one with another.
- Each candidate must include its own `evidence_refs`.
- Mark the candidate that appears more likely, if there is enough evidence.
- Explain why the candidates conflict.

## Evidence Requirements

Every non-empty `explicit`, `inferred`, or `conflict` claim must include
evidence references.

For PDF sources, evidence references should include:

- `source_id`
- `page`
- `locator`
- `quote` or short excerpt in the evidence report

For Markdown or HTML sources, future support should include:

- `source_id`
- `section`
- `line_start`
- `line_end`
- `quote` or short excerpt in the evidence report

Structured files such as `agent_spec.yaml`, `workflow.json`, and `tools.json`
must contain compact `evidence_refs` only. Long quotes and human-readable
explanations belong in `evidence_report.md`.

## Claim Granularity

Evidence should be attached at the smallest practical design unit.

Good examples:

- A module entry has evidence for that module.
- A workflow node has evidence for that step.
- A tool argument has evidence if the source defines it.
- An evaluation setting has evidence for the dataset, metric, and model
  separately when they come from different passages.

Avoid attaching one broad evidence reference to an entire file when individual
claims can be traced more precisely.

## Inference Boundaries

Architecture inference is allowed when it helps readers understand the implied
agent design. Configuration inference is not allowed.

Allowed:

```yaml
agent_type:
  values:
    - rag
    - tool_use
  fidelity: inferred
  rationale: "The source describes retrieving external passages before using an LLM to answer."
  evidence_refs:
    - ev_012
```

Not allowed:

```yaml
model:
  value: "gpt-4.1"
  fidelity: inferred
```

If the source does not name the model, use:

```yaml
model:
  value: null
  fidelity: missing
  impact: "The implementation cannot reproduce model-specific behavior."
```

## Conflict Handling

Conflicts are first-class output, not validation failures by default.

A conflict should become a validation failure only when the package hides the
conflict or writes a single resolved value without preserving competing
candidates.

Example:

```yaml
num_agents:
  fidelity: conflict
  candidates:
    - value: 3
      evidence_refs:
        - ev_021
    - value: 4
      evidence_refs:
        - ev_037
      preferred: true
  conflict_reason: "The architecture figure shows four role labels, while the method text lists three workers."
```

## Validation Rules

Before writing an `agent_package`, the CLI must validate that:

- All non-empty `explicit`, `inferred`, and `conflict` claims have
  `evidence_refs`.
- `inferred` claims include a rationale.
- `missing` claims do not contain invented values.
- `conflict` claims preserve multiple candidates.
- Structured files reference evidence IDs that exist in `evidence_report.md` or
  the package evidence index.
- Concrete configuration values are not marked `inferred`.

The write step must not emit a package that fails these rules unless an explicit
debug or partial-output mode is added in a future version.
