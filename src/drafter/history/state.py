from typing import Any
from dataclasses import dataclass, field
from copy import deepcopy

from drafter.monitor.audit import log_warning


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

        TODO: Throw a warning if there's a type change.

        :param new_state: The new state to set as current.
        """
        if not self.initialized:
            self.initial = deepcopy(new_state)
            self.initialized = True
        elif self.history:
            last_state = self.history[-1]
            if type(last_state) != type(new_state):
                old_type_name = type(last_state).__name__
                new_type_name = type(new_state).__name__
                # TODO: Log additional information about the route
                log_warning(
                    "state.type_change",
                    f"SiteState type changed from {old_type_name} to {new_type_name}.",
                    "site_state.update",
                    f"SiteState type changed from {old_type_name} to {new_type_name}.",
                )
        # TODO: Should these be deep copies?
        self.current = new_state
        self.history.append(new_state)

    def reset(self) -> None:
        """
        Resets the site state to its initial configuration.
        """
        # TODO: Should this be a deep copy?
        self.current = deepcopy(self.initial)
        self.history.clear()
