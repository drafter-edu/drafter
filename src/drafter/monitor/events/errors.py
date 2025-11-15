# TODO: All of these should track request_id, response_id, and outcome_id
# TODO: All of these should have a timestamp

from dataclasses import dataclass
from typing import Optional

from drafter.monitor.events.base import BaseEvent as EventBase


@dataclass
class DrafterLog(EventBase):
    message: str = ""
    where: str = ""
    details: str = ""
    event_type: str = "DrafterLog"

    def to_json(self) -> dict[str, str]:
        return {
            **super().to_json(),
            "message": self.message,
            "where": self.where,
            "details": self.details,
        }


@dataclass
class DrafterError(DrafterLog):
    """
    Represents an error that occurred during processing.
    """

    traceback: Optional[str] = None
    event_type: str = "DrafterError"

    def to_json(self) -> dict:
        return {
            **super().to_json(),
            "traceback": self.traceback,
        }


@dataclass
class DrafterWarning(DrafterLog):
    """
    Represents a warning that occurred during processing.
    """

    traceback: Optional[str] = None
    event_type: str = "DrafterWarning"

    def to_json(self) -> dict:
        return {
            **super().to_json(),
            "traceback": self.traceback,
        }


@dataclass
class DrafterInfo(DrafterLog):
    """
    Represents an informational message during processing.
    """

    event_type: str = "DrafterInfo"

    def to_json(self) -> dict:
        return super().to_json()
