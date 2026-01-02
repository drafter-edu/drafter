from typing import Any
from dataclasses import dataclass, field
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
    _last_state_type: type = None

    def update(self, new_state: Any) -> None:
        """
        Updates the current state and appends the previous state to history.
        
        Emits a warning if the state type changes from the previous update.

        :param new_state: The new state to set as current.
        """
        if not self.initialized:
            self.initial = new_state
            self.initialized = True
            self._last_state_type = type(new_state)
        else:
            # Check for type changes
            new_state_type = type(new_state)
            if self._last_state_type is not None and new_state_type != self._last_state_type:
                old_type_name = self._last_state_type.__name__
                new_type_name = new_state_type.__name__
                log_warning(
                    f"State type changed from {old_type_name} to {new_type_name}. "
                    f"This may indicate an error in your state management."
                )
            self._last_state_type = new_state_type
        
        self.current = new_state
        self.history.append(new_state)

    def reset(self) -> None:
        """
        Resets the site state to its initial configuration.
        """
        # TODO: Should this be a deep copy?
        self.current = self.initial
        self.history.clear()
        self.initialized = False
        self._last_state_type = type(self.initial) if self.initial is not None else None
