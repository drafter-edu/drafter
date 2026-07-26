"""
Tracking of the student's site state over time.

Defines `SiteState`, which wraps the current state value, records every
state in order for the history/debug panel, and remembers the initial
state so it can be restored on reset.
"""

from copy import copy, deepcopy
from dataclasses import dataclass, field
from typing import Any

from drafter.data.errors import CATEGORY_SYSTEM, SEVERITY_WARNING, ErrorDetails
from drafter.monitor.audit import log_error


@dataclass
class SiteState:
    """
    Wrapper for the student's site state.

    Attributes:
        current: The current state of the site, which can be any type.
        history: Every state set via `update`, in order, including the
            current one. Entries are deep copies (falling back to shallow
            copies, then the original reference, when copying fails) so
            that later in-place mutations do not rewrite earlier snapshots.
        initial: A deep copy of the first state ever set, used by `reset`.
        initialized: Whether a first state has been recorded yet.
    """

    current: Any = None
    history: list[Any] = field(default_factory=list)
    initial: Any = None
    initialized: bool = False
    _copy_fallback_reported: bool = field(default=False, repr=False)

    def snapshot(self, value: Any) -> Any:
        """
        Copies a state value for storage, as deeply as possible.

        Tries `copy.deepcopy` first; if that raises (states can hold
        arbitrary objects - open files, locks, lambdas, etc.), falls back
        to a shallow `copy.copy`, and finally to the original reference.
        The first time a fallback happens, a warning is logged via the
        audit system so the student can see why history snapshots may
        share data with the live state.

        Args:
            value: The state value to copy.

        Returns:
            The best available copy of the value.
        """
        try:
            return deepcopy(value)
        except Exception as deep_error:
            try:
                shallow = copy(value)
                self._report_copy_fallback(
                    f"Deep copy failed ({deep_error!r}); fell back to a shallow copy. "
                    f"Nested objects in state history snapshots may share data with the live state."
                )
                return shallow
            except Exception as shallow_error:
                self._report_copy_fallback(
                    f"Deep copy failed ({deep_error!r}) and shallow copy failed ({shallow_error!r}); "
                    f"state history snapshots will share data with the live state."
                )
                return value

    def _report_copy_fallback(self, message: str) -> None:
        """Logs a one-time warning that state snapshots could not be deep-copied."""
        if self._copy_fallback_reported:
            return
        self._copy_fallback_reported = True
        log_error(
            ErrorDetails(
                id="state.copy_fallback",
                category=CATEGORY_SYSTEM,
                message=message,
                severity=SEVERITY_WARNING,
                details=message,
                friendly_message=(
                    "Drafter could not make a full copy of your state for its "
                    "history, so the debugger's history may show values that "
                    "changed later."
                ),
                friendly_steps=(
                    "This usually means the state holds something unusual, like "
                    "an open file or a network connection.",
                    "Keep your state made of simple data (numbers, text, lists, "
                    "and dataclasses) when possible.",
                ),
            ),
            "site_state.snapshot",
        )

    def update(self, new_state: Any) -> None:
        """
        Updates the current state and appends a snapshot of it to history.

        On the first call, the new state is also copied as the initial
        state. If the type of the new state differs from the most recent
        state in history, a warning is logged via the audit system.

        The `current` state keeps the original object (so aliases the
        student holds stay live), while the history entry is a deep copy
        when possible (see `snapshot`).

        Args:
            new_state: The new state to set as current.
        """
        if not self.initialized:
            self.initial = self.snapshot(new_state)
            self.initialized = True
        elif self.history:
            last_state = self.history[-1]
            if type(last_state) is not type(new_state):
                old_type_name = type(last_state).__name__
                new_type_name = type(new_state).__name__
                # TODO: Log additional information about the route
                log_error(
                    ErrorDetails(
                        id="state.type_change",
                        category=CATEGORY_SYSTEM,
                        message=f"SiteState type changed from {old_type_name} to {new_type_name}.",
                        severity=SEVERITY_WARNING,
                        details=f"SiteState type changed from {old_type_name} to {new_type_name}.",
                        friendly_message=(
                            f"One of your routes changed the site state from "
                            f"{old_type_name} to {new_type_name}; the state "
                            "should keep the same type for the whole site."
                        ),
                        friendly_steps=(
                            "Find the route that returned a different kind of "
                            "state value.",
                            "Make every route keep the state as the same type "
                            "(for example, always your State dataclass).",
                        ),
                    ),
                    "site_state.update",
                )
        self.current = new_state
        self.history.append(self.snapshot(new_state))

    def reset(self) -> None:
        """
        Resets the site state to its initial configuration.
        """
        self.current = self.snapshot(self.initial)
        self.history.clear()
