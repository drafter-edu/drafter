"""
Per-instance browser context for the bridge.

A DomContext carries the window and document a Drafter instance renders into.
By default that is the global window/document (the only case before iframes
shared one Pyodide runtime), but an embedding host can hand an instance the
window of its own iframe so every DOM lookup, head injection, event listener,
and history call targets that iframe instead of the top-level page.
"""

from dataclasses import dataclass
from typing import Any

import js


@dataclass
class DomContext:
    """The window and document one Drafter instance targets."""

    window: Any
    document: Any

    @classmethod
    def default(cls) -> "DomContext":
        """Context for the global (top-level) window and document.

        The window is the ``js`` global scope itself rather than ``js.window``
        so this works identically under Skulpt, where only the global scope
        proxy is guaranteed to exist.
        """
        return cls(window=js, document=js.document)

    @classmethod
    def for_window(cls, window: Any) -> "DomContext":
        """Context scoped to a specific window (e.g. an iframe's contentWindow).

        Null-ish values (None, or JS null/undefined proxies, which convert to
        JsNull/JsUndefined rather than None) fall back to the global context.
        """
        document = getattr(window, "document", None) if window is not None else None
        if document is None:
            return cls.default()
        return cls(window=window, document=document)
