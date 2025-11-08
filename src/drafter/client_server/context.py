from typing import Optional
from dataclasses import dataclass, field
from drafter.data.request import Request
from drafter.data.response import Response


@dataclass
class Scope:
    _objs: list = field(default_factory=list)

    def reset(self) -> None:
        """
        Resets the scope by clearing all stored objects.
        """
        self._objs.clear()

    def push(self, obj):
        """
        Pushes a new object onto the scope stack.
        """
        self._objs.append(obj)
        return self

    def pop(self) -> Optional[Request]:
        if self._objs:
            return self._objs.pop()
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.pop()

    def get_current(self) -> Optional[Request]:
        if self._objs:
            return self._objs[-1]
        return None
