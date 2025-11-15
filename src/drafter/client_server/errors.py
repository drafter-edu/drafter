from dataclasses import dataclass
from drafter.monitor.events.errors import DrafterError


@dataclass
class VisitError(Exception):
    error: DrafterError
    status_code: int
