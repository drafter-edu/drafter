"""Response payloads that route functions can return.

Re-exports the payload kinds students use most often (`Page`, `Fragment`,
`Redirect`, `Update`) along with the `ResponsePayload` base class that
defines the payload contract.
"""

from drafter.payloads.kinds.fragment import Fragment
from drafter.payloads.kinds.page import Page
from drafter.payloads.kinds.redirect import Redirect
from drafter.payloads.kinds.update import Update
from drafter.payloads.payloads import ResponsePayload

__all__ = [
    "Page",
    "Fragment",
    "Redirect",
    "Update",
    "ResponsePayload",
]
