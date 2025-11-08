from typing import Optional
from dataclasses import dataclass
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Update(ResponsePayload):
    """
    An Update is a payload that will update the current page's state without
    reloading the entire page. This is useful for making small changes to the
    page dynamically.
    """

    state_update: dict

    def get_state_updates(self) -> tuple[bool, dict]:
        return True, self.state_update

    def render(self, state, configuration) -> Optional[str]:
        return None
