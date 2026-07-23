"""
Runtime adapters for Skulpt and Pyodide differences.
Encapsulates the JS API differences (e.g. .new() constructors, proxy management)
so the rest of the bridge code doesn't need to care about the runtime.
"""

from collections.abc import Callable
from typing import Any

import js
from drafter.bridge.context import DomContext
from drafter.bridge.error_handling import (
    normalize_bridge_exception,
    report_bridge_error,
)
from drafter.helpers.utils import is_pyodide


def create_runtime(context: DomContext | None = None) -> "RuntimeAdapter":
    """Factory: returns the correct runtime adapter for the current environment."""
    if is_pyodide():
        return PyodideRuntime(context)
    return SkulptRuntime(context)


class RuntimeAdapter:
    """Base adapter for runtime-specific JS API calls.

    Holds the instance's DomContext so that window-level operations (history,
    window events, realm-sensitive constructors) target the window this
    instance renders into — which may be an iframe rather than the top page.
    """

    def __init__(self, context: DomContext | None = None):
        self.context = context if context is not None else DomContext.default()

    def _window_class(self, name: str) -> Any:
        """A constructor from the instance's window, or the global fallback.

        Embedding hosts may hand us a bare iframe window that lacks classes
        the Drafter bundle defines (e.g. DebugPanel); fall back to the global
        scope for those.
        """
        window_class = getattr(self.context.window, name, None)
        return window_class if window_class is not None else getattr(js, name)

    def create_debug_panel(
        self, debug_id: str, client_bridge: Any, scope: Any = None
    ) -> Any:
        """Instantiate the JS DebugPanel class for this instance.

        Abstracts constructor invocation across runtimes. The base
        implementation calls the constructor directly, resolving the class
        from the instance's window with a global fallback.

        Args:
            debug_id: DOM id of the debug panel container element.

            client_bridge: The client bridge object handed to the panel.

            scope: Node the panel should scope its lookups to, or None.

        Returns:
            The constructed DebugPanel JS object.
        """
        return self._window_class("DebugPanel")(debug_id, client_bridge, scope)

    def create_url(self, href: str) -> Any:
        """Construct a JS URL object from an href string.

        Abstracts constructor invocation across runtimes; the base
        implementation calls js.URL directly.

        Args:
            href: The URL string to parse.

        Returns:
            The constructed JS URL object.
        """
        return js.URL(href)

    def create_form_data(self, form: Any, submitter: Any = None) -> Any:
        """Construct a JS FormData snapshot of a form.

        Abstracts constructor invocation across runtimes; the base
        implementation calls js.FormData directly.

        Args:
            form: The form element to snapshot.

            submitter: The element that submitted the form (so its
                name/value is included), or None.

        Returns:
            The constructed JS FormData object.
        """
        return js.FormData(form, submitter)

    def convert_to_js(self, obj: Any) -> Any:
        """Convert a Python object to its JS representation.

        Abstracts Python-to-JS value conversion for data handed to JS
        APIs. The base implementation is a passthrough that returns the
        object unchanged.

        Args:
            obj: The Python object to convert.

        Returns:
            The object in a form JS callers can consume.
        """
        return obj

    def wrap_event_handler(self, handler: Callable) -> Any:
        """Prepare a Python callable for use as a JS event listener.

        Abstracts proxy creation for callbacks handed to addEventListener
        and similar APIs. The base implementation is a passthrough that
        returns the handler unchanged.

        Args:
            handler: The Python callable to wrap.

        Returns:
            The listener object to register with JS (here, the handler
            itself).
        """
        return handler

    def cleanup_event_handler(self, handler: Any) -> None:
        """Release runtime resources held by a wrapped event handler.

        Abstracts proxy destruction after a listener produced by
        wrap_event_handler is removed. The base implementation is a no-op.

        Args:
            handler: The wrapped handler previously returned by
                wrap_event_handler.
        """
        pass

    def finish_promises(self, promises: list[Any], afterwards: Callable) -> Any:
        """Run a callback once every pending promise has resolved.

        Abstracts Promise.all-style chaining across runtimes. The base
        implementation assumes the entries are already-resolved values and
        invokes the callback synchronously with the list itself.

        Args:
            promises: The pending promises (or resolved values) to wait
                on.

            afterwards: Callback invoked with the list of resolved values.

        Returns:
            The callback's result (or, in async runtimes, a promise for
            it).
        """
        return afterwards(promises)
        # return js.Promise.all(promises).then(afterwards)

    def promise_data(self, data: dict) -> Any:
        """Wrap response data for return to the JS caller.

        The base implementation returns the data unchanged; runtime
        subclasses may wrap it (e.g. Pyodide returns a resolved JS promise).
        """
        return data

    def thenable(self, promise: Any, afterwards: Callable) -> Any:
        """Chain a callback onto a single promise.

        Abstracts .then() chaining across runtimes. The base
        implementation assumes the value is already resolved and invokes
        the callback synchronously with it.

        Args:
            promise: The promise (or resolved value) to chain onto.

            afterwards: Callback invoked with the resolved value.

        Returns:
            The callback's result (or, in async runtimes, the chained
            promise).
        """
        return afterwards(promise)

    def handle_file_upload(self, file: Any, data: dict, key: str):
        """Read an uploaded JS File and record its contents under a key.

        Abstracts the asynchronous file read across runtimes. Builds a
        file-data dict (filename, content bytes, type, size, and a
        ``__file_upload__`` marker) and stores it at data[key], appending
        to a list when the key already holds a value. The base
        implementation reads the buffer synchronously and returns a
        zero-argument callable that yields the updated mapping.

        Args:
            file: The JS File object to read.

            data: Mapping the file-data dict is written into.

            key: Form field name to store the file data under.

        Returns:
            A completion handle for the read — here a callable returning
            the mapping; async runtimes return a promise instead.
        """
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
        """Push an entry onto the instance window's history.

        Abstracts the state-dict conversion needed before handing it to
        the History API. The base implementation passes the dict through
        unconverted.

        Args:
            state: State object to associate with the history entry.

            title: Title argument for pushState (ignored by browsers).

            url: URL of the new history entry.
        """
        self.context.window.history.pushState(state, title, url)

    def history_replace_state(self, state: dict, title: str, url: str) -> None:
        """Replace the instance window's current history entry.

        Abstracts the state-dict conversion needed before handing it to
        the History API. The base implementation passes the dict through
        unconverted.

        Args:
            state: State object to associate with the history entry.

            title: Title argument for replaceState (ignored by browsers).

            url: URL that replaces the current history entry.
        """
        self.context.window.history.replaceState(state, title, url)

    def create_custom_event(self, name: str, detail: dict) -> Any:
        """Construct a JS CustomEvent carrying a detail payload.

        Abstracts constructor invocation and detail conversion across
        runtimes; the base implementation calls js.CustomEvent directly
        with the Python dict.

        Args:
            name: The event type name.

            detail: Payload placed on the event's detail property.

        Returns:
            The constructed JS CustomEvent object.
        """
        return js.CustomEvent(name, {"detail": detail})

    def dispatch_window_event(self, event: Any) -> None:
        """Dispatch an event on the instance's window.

        Args:
            event: The JS event object to dispatch.
        """
        self.context.window.dispatchEvent(event)


class SkulptRuntime(RuntimeAdapter):
    """Runtime adapter for Skulpt — uses direct JS constructor calls."""

    pass


class PyodideRuntime(RuntimeAdapter):
    """Runtime adapter for Pyodide — uses .new() constructors and proxy management."""

    def __init__(self, context: DomContext | None = None):
        super().__init__(context)
        from pyodide.ffi import create_proxy, to_js

        self._create_proxy = create_proxy
        self._to_js = to_js
        # Stored proxies to prevent garbage collection and enable cleanup
        self._proxies: list[Any] = []

    def create_debug_panel(
        self, debug_id: str, client_bridge: Any, scope: Any = None
    ) -> Any:
        """Pyodide-specific: constructs the DebugPanel via .new()."""
        return self._window_class("DebugPanel").new(debug_id, client_bridge, scope)

    def create_url(self, href: str) -> Any:
        """Pyodide-specific: constructs the URL via js.URL.new()."""
        return js.URL.new(href)

    def create_form_data(self, form: Any, submitter: Any = None) -> Any:
        """Pyodide-specific: constructs the FormData via js.FormData.new()."""
        return js.FormData.new(form, submitter)

    def convert_to_js(self, obj: Any) -> Any:
        """Pyodide-specific: converts via pyodide.ffi.to_js.

        Uses create_pyproxies=False so nested Python objects are converted
        to plain JS values rather than PyProxies that would need explicit
        destruction.
        """
        return self._to_js(obj, create_pyproxies=False)

    def wrap_event_handler(self, handler: Callable) -> Any:
        """Pyodide-specific: wraps the handler in a persistent PyProxy.

        The proxy (from pyodide.ffi.create_proxy) is retained in
        self._proxies to prevent garbage collection while the listener is
        registered and to enable cleanup_event_handler to release it.
        """
        proxy = self._create_proxy(handler)
        self._proxies.append(proxy)
        return proxy

    def cleanup_event_handler(self, handler: Any) -> None:
        """Pyodide-specific: destroys the PyProxy and drops the retained
        reference from self._proxies."""
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
        """Pyodide-specific: chains the callback on a real js.Promise.all.

        The promises are copied into a JS Array (not passed as a PyProxy
        list), failures are routed through _handle_promise_failure, and
        the resulting chain is returned as a persistent proxy so it can be
        handed back to JS safely.
        """
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
        """Pyodide-specific: chains via promise.then(), returning the
        chained promise as a persistent proxy so JS can consume it after
        the call returns."""
        return self._create_proxy(promise.then(afterwards))

    def handle_file_upload(self, file: Any, data: dict, key: str) -> Any:
        """Pyodide-specific: reads the file asynchronously via its
        arrayBuffer() promise.

        Metadata (name, type, size) is read eagerly because the File may
        be a borrowed proxy destroyed after the call; the buffer promise
        is chained to build the file-data dict, and the chain is returned
        as a persistent proxy for use with thenable/finish_promises.
        """
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
        """Pyodide-specific: converts the state dict with to_js before
        calling pushState, since the History API cannot store PyProxies."""
        self.context.window.history.pushState(self._to_js(state), title, url)

    def history_replace_state(self, state: dict, title: str, url: str) -> None:
        """Pyodide-specific: converts the state dict with to_js before
        calling replaceState, since the History API cannot store
        PyProxies."""
        self.context.window.history.replaceState(self._to_js(state), title, url)

    def create_custom_event(self, name: str, detail: dict) -> Any:
        """Pyodide-specific: constructs the event via js.CustomEvent.new(),
        converting the options dict with to_js (create_pyproxies=False) so
        the detail payload is plain JS data."""
        return js.CustomEvent.new(
            name,
            self._to_js({"detail": detail}, create_pyproxies=False),
        )
