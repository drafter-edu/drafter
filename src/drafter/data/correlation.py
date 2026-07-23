"""
Correlation is a grouping context for telemetry events and errors.
"""

from dataclasses import dataclass
from typing import Any, Optional, Dict


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

    causation_id: Optional[int] = None
    route: Optional[str] = None
    request_id: Optional[int] = None
    response_id: Optional[int] = None
    dom_id: Optional[str] = None
    phase: Optional[str] = None

    def to_json(self) -> Dict[str, Any]:
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
