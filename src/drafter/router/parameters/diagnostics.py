"""
Structured diagnostics for the parameter pipeline.

The merge and bind stages report everything that goes wrong (or is merely
suspicious) as `RouteDiagnostic` values instead of raising immediately.
The router then partitions them: warnings are logged, and errors are
raised together as a single `ParameterBindingError` so the debug panel
can explain every problem at once.
"""

from dataclasses import dataclass
from typing import Iterable, Literal

# --- Diagnostics API ---

Severity = Literal["info", "warning", "error"]
"""How serious a diagnostic is; only "error" aborts the request."""

DiagCode = Literal[
    "missing_required_parameter",
    "unused_request_parameter",
    "name_mismatch_suggestion",
    "conversion_failed",
    "payload_collision",
]
"""Stable machine-readable codes identifying each kind of diagnostic."""


@dataclass
class RouteDiagnostic:
    """One problem (or observation) found while binding route parameters.

    Attributes:
        severity: How serious the diagnostic is (info, warning, or error).
        code: Stable machine-readable code identifying the kind of problem.
        route_name: Name of the route function being bound.
        message: Student-facing description of what went wrong.
        parameter: Name of the parameter or payload key involved, if any.
        source: Payload source the value came from (e.g. form_field), if any.
        hint: Student-facing suggestion for how to fix the problem.
        related: Names of other parameters or payload keys involved.
    """

    severity: Severity
    code: DiagCode
    route_name: str
    message: str
    parameter: str = ""
    source: str = ""
    hint: str = ""
    related: tuple[str, ...] = ()


def format_diagnostic(diagnostic: RouteDiagnostic) -> str:
    """One-line student-facing rendering: the message plus its fix hint."""
    if diagnostic.hint:
        return f"{diagnostic.message} {diagnostic.hint}"
    return diagnostic.message


def partition_diagnostics(
    diagnostics: Iterable[RouteDiagnostic],
) -> tuple[tuple[RouteDiagnostic, ...], tuple[RouteDiagnostic, ...]]:
    """Split diagnostics into (errors, non-errors)."""
    errors = tuple(d for d in diagnostics if d.severity == "error")
    others = tuple(d for d in diagnostics if d.severity != "error")
    return errors, others


class ParameterBindingError(ValueError):
    """Raised when a route's parameters cannot be bound or converted.

    Carries the structured diagnostics so the debug panel can explain what
    failed, where the value came from, and how to fix it.
    """

    def __init__(self, diagnostics: Iterable[RouteDiagnostic]):
        self.diagnostics = tuple(diagnostics)
        message = "\n".join(
            format_diagnostic(diagnostic) for diagnostic in self.diagnostics
        )
        super().__init__(message or "Route parameters could not be bound.")
