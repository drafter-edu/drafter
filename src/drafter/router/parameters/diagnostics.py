from dataclasses import dataclass
from typing import Literal

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
