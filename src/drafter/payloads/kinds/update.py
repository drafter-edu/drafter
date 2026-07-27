"""The `Update` payload for changing state without re-rendering the page."""

from dataclasses import dataclass
from typing import Any

from drafter.payloads.payloads import ResponsePayload


@dataclass
class Update(ResponsePayload):
    """
    An Update is a payload that will update the current page's state without
    reloading the entire page. This is useful for making small changes to the
    page dynamically.

    Attributes:
        state_update: The new state value to store in place of the current
            state.

    Example:
        def increment_counter(state):
            return Update(state + 1)
    """

    state_update: Any

    def get_state_updates(self) -> tuple[bool, Any]:
        """Report the state update carried by this payload.

        Returns:
            Tuple of (True, the new state value).
        """
        return True, self.state_update

    def render(self, state, configuration) -> str | None:
        """Render nothing; an Update produces no HTML.

        Args:
            state: Current application state (unused).
            configuration: Server configuration (unused).

        Returns:
            None.
        """
        return None
