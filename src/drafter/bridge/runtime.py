"""
Runtime adapters for Skulpt and Pyodide differences.
Encapsulates the JS API differences (e.g. .new() constructors, proxy management)
so the rest of the bridge code doesn't need to care about the runtime.
"""

import json
import js
from drafter.bridge.log import debug_log
from drafter.bridge.error_handling import (
    normalize_bridge_exception,
    report_bridge_error,
)
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

    def convert_to_js(self, obj: Any) -> Any:
        return obj

    def wrap_event_handler(self, handler: Callable) -> Any:
        return handler

    def cleanup_event_handler(self, handler: Any) -> None:
        pass

    def finish_promises(self, promises: list[Any], afterwards: Callable) -> Any:
        return afterwards(promises)
        # return js.Promise.all(promises).then(afterwards)

    def promise_data(self, data: dict) -> Any:
        """Return a promise that resolves to the provided data (for async handling)."""
        return data

    def thenable(self, promise: Any, afterwards: Callable) -> Any:
        return afterwards(promise)

    def handle_file_upload(self, file: Any, data: dict, key: str):
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

        def return_data():
            return data

        return return_data

    def history_push_state(self, state: dict, title: str, url: str) -> None:
        js.history.pushState(state, title, url)

    def history_replace_state(self, state: dict, title: str, url: str) -> None:
        js.history.replaceState(state, title, url)

    def create_custom_event(self, name: str, detail: dict) -> Any:
        return js.CustomEvent(name, {"detail": detail})

    def dispatch_window_event(self, event: Any) -> None:
        js.dispatchEvent(event)


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

    def convert_to_js(self, obj: Any) -> Any:
        return self._to_js(obj, create_pyproxies=False)

    def wrap_event_handler(self, handler: Callable) -> Any:
        proxy = self._create_proxy(handler)
        self._proxies.append(proxy)
        return proxy

    def cleanup_event_handler(self, handler: Any) -> None:
        if handler is not None and hasattr(handler, "destroy"):
            handler.destroy()
        if handler in self._proxies:
            self._proxies.remove(handler)

    def _handle_promise_failure(self, error: Any) -> None:
        normalized_error = normalize_bridge_exception(error)
        envelope = report_bridge_error(
            "client.promise_resolution_failed",
            "Failed to resolve bridge runtime promises",
            "bridge.runtime.PyodideRuntime.finish_promises",
            f"Original error: {repr(error)}",
            exception=normalized_error,
            phase="event_dispatch",
        )
        raise RuntimeError(envelope.message) from normalized_error

    def finish_promises(self, promises: list[Any], afterwards: Callable) -> Any:
        # Promise.all must receive a real JS array. Passing the Python list
        # directly makes JS iterate a PyProxy, yielding *borrowed* proxies
        # that are destroyed once iteration finishes -- but Promise.all calls
        # .then() on them asynchronously afterwards, causing
        # "This borrowed proxy was automatically destroyed" errors.
        js_promises = js.Array.new()
        for promise in promises:
            js_promises.push(promise)
        chained = (
            js.Promise.all(js_promises)
            .catch(self._handle_promise_failure)
            .then(afterwards)
        )
        # Calling .then()/.catch() from Python yields a PyodideFuture (a
        # Python object), not a JS promise. If this result is handed back to
        # JS (e.g. nested finish_promises for file uploads), it must be a
        # persistent proxy -- otherwise JS receives a borrowed proxy that is
        # destroyed at the end of the call, and Promise.all later fails with
        # "This borrowed proxy was automatically destroyed".
        return self._create_proxy(chained)

    def promise_data(self, data: dict) -> Any:
        """Return a promise that resolves to the provided data (for async handling)."""
        return self._create_proxy(js.Promise.resolve(data))

    def thenable(self, promise: Any, afterwards: Callable) -> Any:
        return self._create_proxy(promise.then(afterwards))

    def handle_file_upload(self, file: Any, data: dict, key: str) -> Any:
        # Read metadata eagerly: `file` may be a borrowed proxy (e.g. yielded
        # by a FormData iterator) that is destroyed once iteration finishes,
        # so it must not be touched inside the async callback below.
        buffer = file.arrayBuffer()
        filename = file.name
        file_type = file.type
        file_size = file.size

        def on_buffer_ready(buffer):
            raw_bytes = js.Uint8Array.new(buffer)
            content = bytes(raw_bytes)
            file_data = {
                "filename": filename,
                "content": content,
                "type": file_type,
                "size": file_size,
                "__file_upload__": True,
            }
            if key not in data:
                data[key] = file_data
            else:
                if not isinstance(data[key], list):
                    data[key] = [data[key]]
                data[key].append(file_data)
            return data

        return self._create_proxy(buffer.then(on_buffer_ready))

    def history_push_state(self, state: dict, title: str, url: str) -> None:
        js.history.pushState(self._to_js(state), title, url)

    def history_replace_state(self, state: dict, title: str, url: str) -> None:
        js.history.replaceState(self._to_js(state), title, url)

    def create_custom_event(self, name: str, detail: dict) -> Any:
        return js.CustomEvent.new(
            name,
            self._to_js({"detail": detail}, create_pyproxies=False),
        )
