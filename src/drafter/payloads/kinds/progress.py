"""Placeholder for the unfinished `Progress` payload.

The `Progress` class is a stub with no behavior yet; it is intended to
eventually report progress on long-running tasks.
"""

from dataclasses import dataclass
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Progress(ResponsePayload):
    """
    A Progress is a payload that can be sent to indicate progress on a long-running
    task.

    TODO: This is not yet ready.
    """
