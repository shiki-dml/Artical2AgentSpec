"""Command-line entry point for Article2AgentSpec.

The CLI is intentionally minimal in the package skeleton. It exists so the
declared console scripts are installable and executable before conversion logic
is implemented.
"""

from __future__ import annotations

from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Run the placeholder CLI entry point."""
    _ = argv
    print(
        "Article2AgentSpec package skeleton.\n"
        "Planned command: article2agentspec convert <paper.pdf>\n"
        "Implementation has not been added yet."
    )
    return 0
