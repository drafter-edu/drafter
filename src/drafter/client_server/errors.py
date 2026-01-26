from dataclasses import dataclass
from drafter.monitor.events.errors import DrafterError


@dataclass
class VisitError(Exception):
    """Wrap an exception arising during a visit lifecycle.

    Attributes:
        error: Domain error captured for reporting.
        status_code: HTTP-like status code associated with the failure.
    """
    error: DrafterError
    status_code: int
