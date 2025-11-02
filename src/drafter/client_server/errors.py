from dataclasses import dataclass
from drafter.data.errors import DrafterError


@dataclass
class VisitError(Exception):
    error: DrafterError
    status_code: int
