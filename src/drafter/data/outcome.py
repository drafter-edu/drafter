from dataclasses import dataclass, field

from drafter.data.errors import DrafterError, DrafterInfo, DrafterWarning


@dataclass
class Outcome:
    id: int
    request_id: int
    response_id: int
    status_code: int = 200
    message: str = "ACK"
    channels: dict = field(default_factory=dict)
    info: list[DrafterInfo] = field(default_factory=list)
    errors: list[DrafterError] = field(default_factory=list)
    warnings: list[DrafterWarning] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
