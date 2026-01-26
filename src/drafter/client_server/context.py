from typing import Optional
from dataclasses import dataclass, field
from drafter.data.request import Request
from drafter.data.response import Response


@dataclass
class Scope:
    """Simple stack-like scope tracker for requests or responses.

    Attributes:
        _objs: Internal stack of scoped objects.
    """

    _objs: list = field(default_factory=list)

    def reset(self) -> None:
        """Reset the scope by clearing stored objects."""
        self._objs.clear()

    def push(self, obj):
        """Push a new object onto the scope stack.

        Args:
            obj: Object to track within the scope.

        Returns:
            Scope: Self for chaining within context managers.
        """
        self._objs.append(obj)
        return self

    def pop(self) -> Optional[Request]:
        """Pop the most recent object from the scope stack.

        Returns:
            Optional[Request]: The popped object or None if empty.
        """
        if self._objs:
            return self._objs.pop()
        return None

    def __enter__(self):
        """Enter context manager and return the scope."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit context manager by popping current object."""
        self.pop()

    def get_current(self) -> Optional[Request]:
        """Return the current scoped object without removing it.

        Returns:
            Optional[Request]: The most recent object or None if empty.
        """
        if self._objs:
            return self._objs[-1]
        return None
