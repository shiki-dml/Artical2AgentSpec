"""Export Article2AgentSpec Pydantic models as JSON Schema files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from schemas.article2agentspec.models import (
        AgentSpec,
        EvalConfig,
        Manifest,
        SourceMetadata,
        ToolsSpec,
        WorkflowSpec,
    )
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
    from schemas.article2agentspec.models import (
        AgentSpec,
        EvalConfig,
        Manifest,
        SourceMetadata,
        ToolsSpec,
        WorkflowSpec,
    )


SCHEMA_EXPORTS = {
    "source_metadata.schema.json": SourceMetadata,
    "agent_spec.schema.json": AgentSpec,
    "workflow.schema.json": WorkflowSpec,
    "tools.schema.json": ToolsSpec,
    "eval_config.schema.json": EvalConfig,
    "manifest.schema.json": Manifest,
}


def export_json_schemas(output_dir: str | Path | None = None) -> list[Path]:
    """Write the public JSON Schema files and return their paths."""
    target_dir = Path(output_dir) if output_dir is not None else Path(__file__).parent / "json_schema"
    target_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for file_name, model in SCHEMA_EXPORTS.items():
        schema_path = target_dir / file_name
        schema = model.model_json_schema()
        schema_path.write_text(
            json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written.append(schema_path)

    return written


def main() -> int:
    """Export schemas to the package json_schema directory."""
    for schema_path in export_json_schemas():
        print(schema_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
