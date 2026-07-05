from dataclasses import dataclass
from typing import Any

from drafter.data.telemetry import TelemetryRecord


@dataclass
class RouteAddedEvent(TelemetryRecord):
    url: str = ""
    signature: str = ""
    is_system_route: bool = False
    kind: str = "RouteAdded"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "url": self.url,
            "signature": self.signature,
            "is_system_route": self.is_system_route,
        }
