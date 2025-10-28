from typing import Any
from dataclasses import dataclass, field


@dataclass
class SiteState:
    """
    Wrapper for the student's site state.

    :ivar current: The current state of the site, which can be any type.
    """

    current: Any = None
    history: list[Any] = field(default_factory=list)
    initial: Any = None
    initialized: bool = False

    def update(self, new_state: Any) -> None:
        """
        Updates the current state and appends the previous state to history.

        :param new_state: The new state to set as current.
        """
        if not self.initialized:
            self.initial = new_state
            self.initialized = True
        self.current = new_state
        self.history.append(new_state)
