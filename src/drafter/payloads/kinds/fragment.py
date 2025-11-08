from typing import Optional
from dataclasses import dataclass
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Fragment(ResponsePayload):
    """
    A Fragment is a payload that will render a fragment of HTML to be injected
    into an existing page, rather than a full page by itself.
    """

    html: str

    def render(self, state, configuration) -> Optional[str]:
        return self.html
