from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml

from article2agentspec.cli import main
from article2agentspec.extraction.heuristic import extract_baseline
from article2agentspec.parsing.pdf import parse_pdf
from article2agentspec.pipeline import convert_pdf
from article2agentspec.validation.validators import validate_package
from article2agentspec.writing.package_writer import REQUIRED_PACKAGE_FILES, write_package
from schemas.article2agentspec.models import WorkflowSpec


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def write_minimal_pdf(path: Path, text: str) -> None:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("ascii")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        (
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        ),
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        b"5 0 obj << /Length " + str(len(content)).encode("ascii") + b" >> stream\n" + content + b"\nendstream endobj\n",
    ]

    chunks = [b"%PDF-1.4\n"]
    offsets = [0]
    offset = len(chunks[0])
    for obj in objects:
        offsets.append(offset)
        chunks.append(obj)
        offset += len(obj)
    xref_offset = offset
    xref = [b"xref\n0 6\n", b"0000000000 65535 f \n"]
    xref.extend(f"{item:010d} 00000 n \n".encode("ascii") for item in offsets[1:])
    trailer = (
        b"trailer << /Size 6 /Root 1 0 R >>\n"
        b"startxref\n"
        + str(xref_offset).encode("ascii")
        + b"\n%%EOF\n"
    )
    path.write_bytes(b"".join(chunks + xref + [trailer]))


def test_parse_pdf_reads_text_metadata_and_page_boundaries(tmp_path: Path) -> None:
    pdf_path = tmp_path / "paper.pdf"
    write_minimal_pdf(pdf_path, "Agent systems use tools.")

    parsed = parse_pdf(pdf_path)

    assert parsed.file_name == "paper.pdf"
    assert parsed.source_id == "src_001"
    assert parsed.file_sha256 is not None
    assert len(parsed.file_sha256) == 64
    assert parsed.page_count == 1
    assert parsed.pages[0].page_number == 1
    assert "Agent systems use tools." in parsed.pages[0].text


def test_pyproject_declares_cli_dependencies_and_console_scripts() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["dependencies"] == [
        "pydantic>=2",
        "pypdf>=5",
        "PyYAML>=6",
    ]
    assert pyproject["project"]["optional-dependencies"]["dev"] == [
        "pytest>=8",
        "ruff>=0.6",
    ]
    assert pyproject["project"]["scripts"] == {
        "article2agentspec": "article2agentspec.cli:main",
        "a2as": "article2agentspec.cli:main",
    }


def test_python_module_entrypoint_exposes_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "article2agentspec", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "usage: article2agentspec" in result.stdout
    assert "convert" in result.stdout


def test_baseline_extraction_builds_missing_heavy_package(tmp_path: Path) -> None:
    pdf_path = tmp_path / "paper.pdf"
    write_minimal_pdf(pdf_path, "Agent systems use tools.")
    parsed = parse_pdf(pdf_path)

    draft = extract_baseline(parsed)

    assert draft.agent_spec.agent.name.fidelity.value == "missing"
    assert draft.workflow.graph.nodes == []
    assert draft.tools.tools == []
    assert draft.eval_config.evaluations == []
    assert "## Page 1" in draft.source_text_md
    assert "Agent systems use tools." in draft.source_text_md
    assert "Baseline extraction" in draft.implementation_notes_md


def test_validation_accepts_baseline_and_rejects_unresolved_evidence(tmp_path: Path) -> None:
    pdf_path = tmp_path / "paper.pdf"
    write_minimal_pdf(pdf_path, "Agent systems use tools.")
    draft = extract_baseline(parse_pdf(pdf_path))

    valid_result = validate_package(draft)

    assert valid_result.passed is True
    assert valid_result.errors == []

    draft.workflow = WorkflowSpec(evidence_refs=["ev_missing"])
    invalid_result = validate_package(draft)

    assert invalid_result.passed is False
    assert any("ev_missing" in error for error in invalid_result.errors)


def test_writer_outputs_required_files_and_debug_artifacts(tmp_path: Path) -> None:
    pdf_path = tmp_path / "paper.pdf"
    write_minimal_pdf(pdf_path, "Agent systems use tools.")
    draft = extract_baseline(parse_pdf(pdf_path))
    validation_result = validate_package(draft)

    package_dir = write_package(draft, tmp_path / "outputs", validation_result, debug=True)

    assert package_dir == tmp_path / "outputs" / "paper"
    assert {path.name for path in package_dir.iterdir() if path.is_file()} >= set(REQUIRED_PACKAGE_FILES)
    yaml.safe_load((package_dir / "manifest.yaml").read_text(encoding="utf-8"))
    yaml.safe_load((package_dir / "source_metadata.yaml").read_text(encoding="utf-8"))
    yaml.safe_load((package_dir / "agent_spec.yaml").read_text(encoding="utf-8"))
    json.loads((package_dir / "workflow.json").read_text(encoding="utf-8"))
    json.loads((package_dir / "tools.json").read_text(encoding="utf-8"))
    yaml.safe_load((package_dir / "eval_config.yaml").read_text(encoding="utf-8"))
    assert (package_dir / "debug" / "raw_pdf_parse.json").exists()
    assert (package_dir / "debug" / "validation_report.json").exists()


def test_pipeline_runs_complete_conversion(tmp_path: Path) -> None:
    pdf_path = tmp_path / "paper.pdf"
    write_minimal_pdf(pdf_path, "Agent systems use tools.")

    package_dir = convert_pdf(pdf_path, output_root=tmp_path / "outputs", debug=True)

    assert package_dir == tmp_path / "outputs" / "paper"
    assert {path.name for path in package_dir.iterdir() if path.is_file()} >= set(REQUIRED_PACKAGE_FILES)


def test_cli_reports_runtime_errors(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    exit_code = main(["convert", str(tmp_path / "missing.pdf")])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error: input file does not exist" in captured.err

    not_pdf = tmp_path / "paper.txt"
    not_pdf.write_text("not a pdf", encoding="utf-8")

    exit_code = main(["convert", str(not_pdf)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error: input file is not a PDF" in captured.err


def test_cli_runs_successful_conversion(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    pdf_path = tmp_path / "paper.pdf"
    write_minimal_pdf(pdf_path, "Agent systems use tools.")

    exit_code = main(["convert", str(pdf_path), "-o", str(tmp_path / "outputs"), "--debug"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"Wrote agent package: {tmp_path / 'outputs' / 'paper'}" in captured.out
    package_dir = tmp_path / "outputs" / "paper"
    assert {path.name for path in package_dir.iterdir() if path.is_file()} >= set(REQUIRED_PACKAGE_FILES)
    assert (package_dir / "debug" / "raw_pdf_parse.json").exists()
    assert (package_dir / "debug" / "validation_report.json").exists()
