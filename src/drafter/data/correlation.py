"""
Correlation is a grouping context for telemetry events and errors.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Correlation:
    """
    Correlation information for telemetry events and errors.

    Attributes:
        causation_id: The ID of the causation event; if this event was caused by another event.
        route: The route name/url associated with the event
        request_id: The ID of the associated request
        response_id: The ID of the associated response
        dom_id: The ID of the associated DOM element if this came from the Bridge Client.
        phase: The phase of the event within the request lifecycle (e.g., "initial", "processing", "final").
    """

    causation_id: int | None = None
    route: str | None = None
    request_id: int | None = None
    response_id: int | None = None
    dom_id: str | None = None
    phase: str | None = None

    def to_json(self) -> dict[str, Any]:
        """
        Converts the Correlation instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the Correlation.
        """
        return {
            "causation_id": self.causation_id,
            "route": self.route,
            "request_id": self.request_id,
            "response_id": self.response_id,
            "dom_id": self.dom_id,
            "phase": self.phase,
        }
