"""
Runtime adapters for Skulpt and Pyodide differences.
Encapsulates the JS API differences (e.g. .new() constructors, proxy management)
so the rest of the bridge code doesn't need to care about the runtime.
"""

import json
import js
from drafter.bridge.log import debug_log
from drafter.constants import SUBMIT_BUTTON_KEY
from drafter.data.request import Request
from drafter.site.site import DRAFTER_TAG_IDS
from drafter.helpers.utils import is_pyodide
from typing import Callable, Any, Optional


def create_runtime() -> "RuntimeAdapter":
    """Factory: returns the correct runtime adapter for the current environment."""
    if is_pyodide():
        return PyodideRuntime()
    return SkulptRuntime()


class RuntimeAdapter:
    """Base adapter for runtime-specific JS API calls."""

    def create_debug_panel(self, debug_id: str, client_bridge: Any) -> Any:
        return js.DebugPanel(debug_id, client_bridge)

    def create_url(self, href: str) -> Any:
        return js.URL(href)

    def create_form_data(self, form: Any, submitter: Any = None) -> Any:
        return js.FormData(form, submitter)

    def wrap_event_handler(self, handler: Callable) -> Any:
        return handler

    def cleanup_event_handler(self, handler: Any) -> None:
        pass

    def handle_file_upload(self, file: Any, data: dict, key: str) -> None:
        buffer = file.arrayBuffer()
        raw_bytes = js.Uint8Array(buffer)
        content = bytes(raw_bytes)
        file_data = {
            "filename": file.name,
            "content": content,
            "type": file.type,
            "size": file.size,
            "__file_upload__": True,
        }
        if key not in data:
            data[key] = file_data
        else:
            if not isinstance(data[key], list):
                data[key] = [data[key]]
            data[key].append(file_data)

    def history_push_state(self, state: dict, title: str, url: str) -> None:
        js.history.pushState(state, title, url)


class SkulptRuntime(RuntimeAdapter):
    """Runtime adapter for Skulpt — uses direct JS constructor calls."""
    pass


class PyodideRuntime(RuntimeAdapter):
    """Runtime adapter for Pyodide — uses .new() constructors and proxy management."""

    def __init__(self):
        from pyodide.ffi import create_proxy, to_js
        self._create_proxy = create_proxy
        self._to_js = to_js
        # Stored proxies to prevent garbage collection and enable cleanup
        self._proxies: list[Any] = []

    def create_debug_panel(self, debug_id: str, client_bridge: Any) -> Any:
        return js.DebugPanel.new(debug_id, client_bridge)

    def create_url(self, href: str) -> Any:
        return js.URL.new(href)

    def create_form_data(self, form: Any, submitter: Any = None) -> Any:
        return js.FormData.new(form, submitter)

    def wrap_event_handler(self, handler: Callable) -> Any:
        proxy = self._create_proxy(handler)
        self._proxies.append(proxy)
        return proxy

    def cleanup_event_handler(self, handler: Any) -> None:
        if handler is not None and hasattr(handler, "destroy"):
            handler.destroy()
        if handler in self._proxies:
            self._proxies.remove(handler)

    def handle_file_upload(self, file: Any, data: dict, key: str) -> None:
        # TODO: Implement async file handling for Pyodide
        raise NotImplementedError(
            "Async file upload handling in Pyodide not implemented yet."
        )

    def history_push_state(self, state: dict, title: str, url: str) -> None:
        js.history.pushState(self._to_js(state), title, url)
