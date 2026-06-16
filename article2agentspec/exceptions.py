"""Project-specific exceptions for CLI-facing failures."""

from __future__ import annotations


class Article2AgentSpecError(Exception):
    """Base class for expected Article2AgentSpec runtime failures."""


class InputError(Article2AgentSpecError):
    """Raised when the input source cannot be accepted."""


class ParseError(Article2AgentSpecError):
    """Raised when a source file cannot be parsed."""


class ValidationFailure(Article2AgentSpecError):
    """Raised when extracted package data fails validation."""


class WriteError(Article2AgentSpecError):
    """Raised when a validated package cannot be written."""
