from dataclasses import dataclass
from typing import Iterable, Literal

# --- Diagnostics API ---

Severity = Literal["info", "warning", "error"]
DiagCode = Literal[
    "missing_required_parameter",
    "unused_request_parameter",
    "name_mismatch_suggestion",
    "conversion_failed",
    "payload_collision",
]


@dataclass
class RouteDiagnostic:
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
