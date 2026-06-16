"""Command-line entry point for Article2AgentSpec."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from article2agentspec.exceptions import Article2AgentSpecError
from article2agentspec.pipeline import convert_pdf


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "convert":
            package_dir = convert_pdf(
                Path(args.source_pdf),
                output_root=Path(args.output_root),
                debug=args.debug,
            )
            print(f"Wrote agent package: {package_dir}")
            return 0
    except Article2AgentSpecError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.error("unknown command")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="article2agentspec",
        description="Convert LLM agent architecture PDFs into evidence-grounded agent packages.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser("convert", help="convert a local PDF into an agent package")
    convert_parser.add_argument("source_pdf", help="local PDF file to convert")
    convert_parser.add_argument(
        "-o",
        "--output-root",
        default="outputs",
        help="output root directory, defaults to outputs",
    )
    convert_parser.add_argument(
        "--debug",
        action="store_true",
        help="write debug artifacts under the package debug directory",
    )

    return parser
