"""
Route registration events for tracking which routes the server knows about.
"""

from dataclasses import dataclass, field
from typing import Any

from drafter.data.telemetry import TelemetryRecord


@dataclass
class RouteAddedEvent(TelemetryRecord):
    """
    Event emitted when a route is registered with the server.

    Attributes:
        url: The URL path of the added route
        signature: String rendering of the route function's signature
        parameters: Structured request-parameter metadata (name/type/
            required/default dicts) so the debug panel can build parameter
            forms for the route
        is_system_route: Whether the route was registered by the framework
            itself rather than by user code
        kind: Event-type discriminator, always "RouteAdded"
    """

    url: str = ""
    signature: str = ""
    parameters: list[dict] = field(default_factory=list)
    is_system_route: bool = False
    kind: str = "RouteAdded"

    def to_json(self) -> dict[str, Any]:
        """
        Converts the RouteAddedEvent instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the event.
        """
        return {
            **super().to_json(),
            "url": self.url,
            "signature": self.signature,
            "parameters": self.parameters,
            "is_system_route": self.is_system_route,
        }
