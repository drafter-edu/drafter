# TODO: All of these should track request_id, response_id, and outcome_id
# TODO: All of these should have a timestamp

from dataclasses import dataclass


@dataclass
class DrafterLog:
    message: str
    where: str
    details: str


@dataclass
class DrafterError(DrafterLog):
    """
    Represents an error that occurred during processing.
    """

    traceback: str


@dataclass
class DrafterWarning(DrafterLog):
    """
    Represents a warning that occurred during processing.
    """

    traceback: str


@dataclass
class DrafterInfo(DrafterLog):
    """
    Represents an informational message during processing.
    """
