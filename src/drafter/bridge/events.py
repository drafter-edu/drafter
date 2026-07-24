"""Browser event wiring and form-data collection for the bridge.

The :class:`EventManager` attaches the DOM listeners that turn browser
activity into router dispatches: delegated click navigation (``data-nav`` /
``data-call``), form submission, per-component event handlers declared via
the ``data--drafter-handlers`` attribute, global window events, and
double-press hotkeys. The module-level functions gather everything a
dispatch needs from the DOM — form values (including asynchronous file
uploads), custom event details, and component argument attributes — and
package them into the ``{"values": ..., "payload": ...}`` envelope that
handlers pass to the router, with per-value provenance entries so the
router can merge by precedence (component arguments > event detail > form
fields) and report collisions.
"""

import json
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import js
from drafter.bridge.dom import (
    get_attribute_recursively,
)
from drafter.bridge.error_handling import (
    raise_bridge_system_error,
    report_bridge_error,
    report_bridge_warning,
)
from drafter.bridge.log import debug_log
from drafter.bridge.runtime import RuntimeAdapter
from drafter.components.page_content import Component
from drafter.data.request import Request
from drafter.site.site import DRAFTER_TAG_IDS

DOUBLE_PRESS_THRESHOLD = 600  # milliseconds
"""Maximum gap, in milliseconds, between two presses of a hotkey combination
for them to count as a double press and trigger the hotkey's callback."""

DRAFTER_PAGE_LOADED_EVENT = "drafter-page-loaded"
"""Name of the custom window event dispatched after each page render,
carrying the route, request id, and response id in its detail."""

# Set on an element once its per-element handlers are attached. Persisted
# components survive page swaps with their listeners intact, so re-mounting on
# a later page load would dispatch every event twice (and leak listeners).
HANDLERS_MOUNTED_ATTR = "data-drafter-handlers-mounted"
"""Attribute set on an element once its per-element handlers are attached.

Persisted components survive page swaps with their listeners intact, so
re-mounting on a later page load would dispatch every event twice (and leak
listeners); this marker lets ``mount_event_handlers`` skip them.
"""


@dataclass
class EventManager:
    """Manages the DOM event listeners for one Drafter instance.

    Mounts navigation click/submit delegation, per-component event handlers,
    global window events, and hotkeys, wrapping every callback through the
    runtime adapter so proxies are created and cleaned up correctly. Lookups
    for the instance's inner-frame elements (BODY/FORM) are scoped so that
    concurrent instances on the same page don't find each other's elements.

    Attributes:
        runtime: Runtime adapter used to wrap, clean up, and chain the
            event handlers and their promises.

        click_handler: The currently mounted (wrapped) delegated click
            handler on the body element, or None before mounting.

        submit_handler: The currently mounted (wrapped) submit handler on
            the form element, or None before mounting.

        listeners: Wrapped window-level listeners keyed by event name, kept
            so re-registration can remove and clean up the old handler.

        hotkey_events: Callbacks keyed by lowercase key name, triggered on
            a double press of Ctrl/Meta plus that key.

        last_press_time: Timestamp in milliseconds of the last qualifying
            hotkey press, used to detect double presses.

        hotkey_listener_ready: Whether the shared keydown listener backing
            all hotkeys has been attached to the document.

        scope: Node that inner-frame lookups (BODY/FORM) are scoped to;
            defaults to the instance's document and is replaced with the
            instance's shadow root via set_scope().
    """

    runtime: RuntimeAdapter
    click_handler: Any = None
    submit_handler: Any = None
    listeners: dict[str, Callable] = field(default_factory=dict)
    hotkey_events: dict[str, Callable[[], None]] = field(default_factory=dict)
    last_press_time: int = 0
    hotkey_listener_ready: bool = False

    def __init__(self, runtime: RuntimeAdapter):
        self.runtime = runtime
        self.click_handler = None
        self.submit_handler = None
        self.listeners = {}

        self.hotkey_events = {}
        self.last_press_time = 0
        self.hotkey_listener_ready = False
        # The wrapped keydown listener backing all hotkeys, kept so teardown
        # can remove it from the document and release its proxy.
        self.hotkey_listener: Any = None
        # The node inner-frame lookups (BODY/FORM) are scoped to. Defaults to
        # the instance's document (the iframe's document for embedded
        # instances); set to the instance's shadow root by set_scope() so
        # concurrent instances don't find each other's elements.
        self.scope: Any = runtime.context.document

    def set_scope(self, scope: Any) -> None:
        """Scope this manager's inner-frame lookups to the given node."""
        if scope is not None:
            self.scope = scope

    # Event Mounts

    def mount_event_handlers(self, root: Any, do_navigation: Callable):
        """Mount event handlers for components with data--drafter-handlers attribute.

        This sets up delegation for events like blur, change, focus, input, etc.,
        that should trigger route dispatches.

        Args:
            root: The root element to attach listeners to.
            do_navigation: Callback to handle navigation events.
        """
        debug_log("client.mount_event_handlers")

        elements_with_handlers = root.querySelectorAll(
            f"[{Component.DRAFTER_DATA_HANDLERS_NAME}]"
        )

        for element in elements_with_handlers:
            if element.getAttribute(HANDLERS_MOUNTED_ATTR):
                continue
            handlers_json = element.getAttribute(Component.DRAFTER_DATA_HANDLERS_NAME)
            if not handlers_json:
                continue

            try:
                handlers = json.loads(handlers_json)
            except Exception as e:
                report_bridge_error(
                    "bridge.event_handlers_parse_failed",
                    "Failed to parse component event handlers attribute; skipping element",
                    "bridge.events.mount_event_handlers",
                    f"Attribute value: {handlers_json}",
                    exception=e,
                    dom_id=element.id if hasattr(element, "id") else None,
                    phase="setup",
                )
                continue
            # For each event type in the handlers
            for event_type, route_name in handlers.items():
                # Create a handler function for this event
                def make_handler(event_name, route):
                    def handler(event):
                        debug_log(f"client.event_handler.{event_name}", event)

                        # Don't prevent default for most events (except clicks handled elsewhere)
                        target_element = event.target
                        dom_id = (
                            target_element.id if hasattr(target_element, "id") else None
                        )

                        incomplete_data = get_all_event_data(
                            self.runtime, target_element, event, None, self.scope
                        )

                        def finish_navigation(files_and_data):
                            bundle = files_and_data[-1] if files_and_data else {}
                            data, raw_payload = unpack_event_bundle(bundle)
                            request = Request(
                                action=event_name,
                                url=route,
                                kwargs=data,
                                event={},  # TODO: Populate this with useful event info
                                dom_id=dom_id or "",
                                button_pressed=target_element,
                                raw_payload=raw_payload,
                            )
                            try:
                                return do_navigation(request)
                            except Exception as e:
                                report_bridge_error(
                                    "bridge.event_dispatch_failed",
                                    f"Failed to dispatch {event_name} event to route {route}",
                                    "bridge.events.mount_event_handlers",
                                    f"Request: {repr(request)}",
                                    exception=e,
                                    route=request.url,
                                    dom_id=request.dom_id,
                                    request_id=request.id,
                                    phase="event_dispatch",
                                )

                        self.runtime.finish_promises(incomplete_data, finish_navigation)

                    return handler

                wrapped_handler = self.runtime.wrap_event_handler(
                    make_handler(event_type, route_name)
                )
                element.addEventListener(event_type, wrapped_handler)
                debug_log("client.event_handler_added", event_type, element)
            element.setAttribute(HANDLERS_MOUNTED_ATTR, "true")

    def mount_navigation(self, do_navigation: Callable):
        """Mount the delegated click and form-submit listeners for navigation.

        Attaches a click handler to the instance's body element that
        intercepts clicks on elements carrying data-nav or data-call and
        turns them into "link" requests, and a submit handler on the
        instance's form element that turns submissions into "form" requests
        (resolving the target URL from the submitter's formaction, the
        form's action, or the current location). Previously mounted click
        handlers are removed and cleaned up first, and per-component event
        handlers are (re)mounted via mount_event_handlers. Both handlers
        collect event/form/argument data, wait for any pending file-upload
        promises, then invoke the navigation callback.

        Args:
            do_navigation: Callback invoked with the built Request to
                perform the route dispatch.

        Raises:
            RuntimeError: If the instance's form root element cannot be
                found (via raise_bridge_system_error).
        """
        debug_log("client.mount_navigation")
        # Get the body element (scoped to this instance's shadow root)
        root = self.scope.querySelector("#" + DRAFTER_TAG_IDS["BODY"])
        # Clean up old handlers if they exist
        if self.click_handler is not None:
            root.removeEventListener("click", self.click_handler)
            self.runtime.cleanup_event_handler(self.click_handler)

        # Store the navigation callback
        def handle_click(event: Any):
            target = event.target
            if not target:
                return

            # Find nearest element with data-nav or data-call
            nearest_nav_link = target.closest("[data-nav], [data-call]")
            if nearest_nav_link and root.contains(nearest_nav_link):
                event.preventDefault()
                debug_log("client.handle_click", nearest_nav_link)
                name = nearest_nav_link.getAttribute(
                    "data-nav"
                ) or nearest_nav_link.getAttribute("data-call")
                if not name:
                    return

                dom_id = (
                    nearest_nav_link.id if hasattr(nearest_nav_link, "id") else None
                )

                is_anchor = nearest_nav_link.tagName.lower() == "a"
                incomplete_data = get_all_event_data(
                    self.runtime,
                    target,
                    event,
                    None if is_anchor else nearest_nav_link,
                    self.scope,
                )

                def finish_navigation(files_and_data):
                    bundle = files_and_data[-1] if files_and_data else {}
                    data, raw_payload = unpack_event_bundle(bundle)
                    request = Request(
                        action="link",
                        url=name,
                        kwargs=data,
                        event={},  # TODO: Populate this with useful event info
                        dom_id=dom_id or "",
                        button_pressed=nearest_nav_link if not is_anchor else "",
                        raw_payload=raw_payload,
                    )
                    try:
                        return do_navigation(request)
                    except Exception as e:
                        report_bridge_error(
                            "client.navigation_failed",
                            "Failed to dispatch navigation request",
                            "bridge.events.mount_navigation",
                            f"Request: {repr(request)}",
                            exception=e,
                            route=request.url,
                            dom_id=request.dom_id,
                            request_id=request.id,
                            phase="navigation",
                        )

                self.runtime.finish_promises(incomplete_data, finish_navigation)

        def submit_handler(event: Any):
            debug_log("client.form_submit_handler", event)
            event.preventDefault()
            # Figure out submitter
            if hasattr(event, "submitter"):
                submitter = event.submitter
                dom_id = (
                    submitter.id if submitter and hasattr(submitter, "id") else None
                )
            else:
                submitter = None
                dom_id = None
            if submitter is not None and hasattr(submitter, "getAttribute"):
                url = submitter.getAttribute("formaction")
            elif hasattr(form_root, "action"):
                url = form_root.action
            else:
                url = self.runtime.context.window.location.href
            # Build and dispatch navigation event
            incomplete_data = get_all_event_data(
                self.runtime, event.target, event, submitter, self.scope
            )

            def finish_form_navigation(files_and_data):
                # Like the other handlers, this receives the resolved list of
                # promises; the last entry is the event-data envelope. (The
                # previous version passed the whole list as kwargs.)
                bundle = files_and_data[-1] if files_and_data else {}
                data, raw_payload = unpack_event_bundle(bundle)
                request = Request(
                    action="form",
                    url=url,
                    kwargs=data,
                    event={},  # TODO: Populate this with useful event info
                    dom_id=dom_id or "",
                    button_pressed=submitter if submitter else "",
                    raw_payload=raw_payload,
                )
                try:
                    return do_navigation(request)
                except Exception as e:
                    report_bridge_error(
                        "client.navigation_failed",
                        "Failed to dispatch form submission request",
                        "bridge.events.mount_navigation",
                        f"Request: {repr(request)}",
                        exception=e,
                        route=request.url,
                        dom_id=request.dom_id,
                        request_id=request.id,
                        phase="navigation",
                    )

            self.runtime.finish_promises(incomplete_data, finish_form_navigation)

        self.click_handler = self.runtime.wrap_event_handler(handle_click)
        self.submit_handler = self.runtime.wrap_event_handler(submit_handler)

        root.addEventListener("click", self.click_handler)

        form_root = self.scope.querySelector("#" + DRAFTER_TAG_IDS["FORM"])
        if form_root:
            form_root.addEventListener("submit", self.submit_handler)
        else:
            raise_bridge_system_error(
                "client.form_root_missing",
                "Form root element not found while mounting navigation",
                "bridge.events.mount_navigation",
                f"Expected form id: {DRAFTER_TAG_IDS['FORM']}",
                phase="setup",
            )

        # Mount event handlers for components
        self.mount_event_handlers(root, do_navigation)
        debug_log("client.mount_navigation_complete")

    def mount_subtle_debug_entry(self, callback: Callable[[], None]) -> None:
        """Wire the subtle production debug-entry button to the debug toggle.

        Bound here with a proper proxied listener (not an inline onclick in the
        site HTML) so the click is handled by this instance's own bridge no
        matter which document (e.g. an iframe) the site renders into.
        """
        button = self.scope.querySelector("#" + DRAFTER_TAG_IDS["SUBTLE_DEBUG_ENTRY"])
        if not button:
            return
        wrapped_handler = self.runtime.wrap_event_handler(lambda event: callback())
        button.addEventListener("click", wrapped_handler)
        debug_log("client.subtle_debug_entry_mounted")

    ### Global Event Handler Registration
    def setup_events(
        self,
        event_handlers: dict[str, Callable[[Any], Any]],
        key_handlers: dict[str, Callable[[], None]],
    ) -> None:
        """Register global window event listeners and hotkey callbacks.

        Args:
            event_handlers: Mapping from window event name to the handler
                to invoke; each is wrapped and attached to the window,
                replacing any previously registered handler for that name.

            key_handlers: Mapping from key combination (e.g. "ctrl+d") to
                the callback triggered on a double press of that hotkey.
        """
        debug_log("client.setup_events")

        # Global events
        for event_name, event_handler in event_handlers.items():
            self._register_event(event_name, event_handler)

        # Keyboard events
        for key_combo, key_handler in key_handlers.items():
            self._register_hotkey(key_combo, key_handler)

    def dispatch_page_loaded(
        self, route: str, request_id: int, response_id: int
    ) -> None:
        """Dispatch the drafter-page-loaded custom event on the window.

        Fired after a page render so external code (e.g. tests or embedding
        hosts) can observe that a route finished loading.

        Args:
            route: Name of the route that was rendered.

            request_id: Identifier of the request that produced the page.

            response_id: Identifier of the response that was rendered.
        """
        detail = {
            "route": route,
            "requestId": request_id,
            "responseId": response_id,
        }
        event = self.runtime.create_custom_event(DRAFTER_PAGE_LOADED_EVENT, detail)
        self.runtime.dispatch_window_event(event)
        debug_log("client.page_loaded_event_dispatched", detail)

    def _register_event(self, event_name: str, handler: Callable[[Any], Any]) -> None:
        window = self.runtime.context.window
        if self.listeners.get(event_name):
            window.removeEventListener(event_name, self.listeners[event_name])
            self.runtime.cleanup_event_handler(self.listeners[event_name])
        wrapped_handler = self.runtime.wrap_event_handler(handler)
        window.addEventListener(event_name, wrapped_handler)
        self.listeners[event_name] = wrapped_handler

    def _register_hotkey(self, key_combo: str, callback: Callable[[], None]) -> None:
        debug_log("client.register_hotkey", key_combo)
        key = key_combo.lower().split("+")[-1].strip()

        def hotkey_handler(event: Any):
            event_key = event.key.lower() if hasattr(event, "key") else ""
            ctrl = getattr(event, "ctrlKey", False) or getattr(event, "metaKey", False)

            if ctrl and event_key in self.hotkey_events:
                current_time = int(time.time() * 1000)
                time_since_last = current_time - self.last_press_time

                if time_since_last < DOUBLE_PRESS_THRESHOLD:
                    debug_log("client.hotkey_triggered", event_key)
                    event.preventDefault()
                    self.hotkey_events[event_key]()
                    self.last_press_time = 0  # Reset to avoid triple presses being treated as double presses
                else:
                    self.last_press_time = current_time

        self.hotkey_events[key] = callback
        if not self.hotkey_listener_ready:
            wrapped_handler = self.runtime.wrap_event_handler(hotkey_handler)
            self.runtime.context.document.addEventListener("keydown", wrapped_handler)
            self.hotkey_listener = wrapped_handler
            self.hotkey_listener_ready = True
            debug_log("client.hotkey_listener_registered")

    def teardown(self) -> None:
        """Remove this manager's window/document listeners and release them.

        Called when the instance is torn down (e.g. before its code is re-run
        by the in-browser editor). Without this, the old instance's global
        listeners survive its DOM and keep routing events into its dead
        bridge. Element-level listeners (click/submit/component handlers) die
        with the instance's DOM and need no removal here; their proxies are
        released so the runtime does not retain them.
        """
        window = self.runtime.context.window
        for event_name, handler in list(self.listeners.items()):
            try:
                window.removeEventListener(event_name, handler)
            except Exception:
                # The window may already be gone (e.g. a removed iframe).
                pass
            self.runtime.cleanup_event_handler(handler)
        self.listeners.clear()

        if self.hotkey_listener is not None:
            try:
                self.runtime.context.document.removeEventListener(
                    "keydown", self.hotkey_listener
                )
            except Exception:
                pass
            self.runtime.cleanup_event_handler(self.hotkey_listener)
            self.hotkey_listener = None
        self.hotkey_listener_ready = False
        self.hotkey_events.clear()

        for handler in (self.click_handler, self.submit_handler):
            if handler is not None:
                self.runtime.cleanup_event_handler(handler)
        self.click_handler = None
        self.submit_handler = None
        debug_log("client.event_manager_teardown")


def get_single_checkbox_names(form: Any) -> set[str]:
    """Get the names of checkbox fields that appear exactly once in a form.

    Single checkboxes are special-cased by normalize_form_data: when
    unchecked they submit no value at all, so their absence is coerced to
    False rather than being omitted.

    Args:
        form: The form element whose controls are inspected.

    Returns:
        Set of field names belonging to exactly one checkbox input.
    """
    checkbox_counts: Counter[str] = Counter()

    for element in form.elements:
        name = str(getattr(element, "name", "") or "")
        tag_name = str(getattr(element, "tagName", "") or "").lower()
        input_type = str(getattr(element, "type", "") or "").lower()

        if name and tag_name == "input" and input_type == "checkbox":
            checkbox_counts[name] += 1

    return {name for name, count in checkbox_counts.items() if count == 1}


def get_multiple_field_names(form: Any) -> set[str]:
    """Get the names of all form fields that can have multiple values."""

    multiple_names: set[str] = set()
    checkbox_counts: Counter[str] = Counter()

    for element in form.elements:
        name = str(getattr(element, "name", "") or "")
        if not name:
            continue

        tag_name = str(getattr(element, "tagName", "") or "").lower()
        input_type = str(getattr(element, "type", "") or "").lower()

        if tag_name == "input" and input_type == "checkbox":
            checkbox_counts[name] += 1

        if tag_name == "select" and bool(getattr(element, "multiple", False)):
            multiple_names.add(name)

        if (
            tag_name == "input"
            and input_type == "file"
            and bool(getattr(element, "multiple", False))
        ):
            multiple_names.add(name)

        if element.getAttribute("data-cardinality") == "many":
            multiple_names.add(name)

    multiple_names.update(name for name, count in checkbox_counts.items() if count > 1)

    return multiple_names


def group_form_data(
    form: Any,
    form_data: Any,
) -> tuple[dict[str, list[Any]], set[str]]:
    """
    Convert FormData into its natural Python representation:
    a mapping from names to lists of submitted values.
    """
    multiple_names = get_multiple_field_names(form)
    names = {str(name) for name in form_data.keys()} | multiple_names
    grouped = {name: list(form_data.getAll(name)) for name in names}

    return grouped, multiple_names


def normalize_form_data(
    grouped: dict[str, list[Any]],
    multiple_names: set[str],
    single_checkbox_names: set[str],
) -> dict[str, Any]:
    """
    Multi-valued fields are always lists. Scalar fields are scalars unless
    malformed or duplicate controls submitted more than one value.
    """
    normalized: dict[str, Any] = {}

    for name, values in grouped.items():
        if name in multiple_names:
            normalized[name] = values
        elif len(values) == 1:
            normalized[name] = values[0]
        elif len(values) > 1:
            # TODO: Decide if this should be an error/warning, or if it should be promoted
            normalized[name] = values
        elif name in single_checkbox_names:
            normalized[name] = bool(values)

    # # First convert all form data to a regular dict, handling file uploads as well
    # for key, value in form_data.entries():
    #     if isinstance(value, str):
    #         if key in data:
    #             if not isinstance(data[key], list):
    #                 data[key] = [data[key]]
    #             data[key].append(value)
    #         else:
    #             data[key] = value
    #     else:
    #         # TODO: Need to make this part of a chaining promise to handle async pyodide uploads
    #         incomplete_resolutions.append(
    #             runtime.handle_file_upload(value, data, key)
    #         )

    return normalized


def json_decode_form_value(
    key: str,
    value: Any,
    *,
    element: Any,
) -> Any:
    """JSON-decode a form field value, falling back to the raw value.

    Applied to fields whose element carries data-transform="json-decode"
    (e.g. JSON-encoded component arguments). List values are decoded
    item by item; non-string items (e.g. file uploads) are passed through
    unchanged. A value that fails to decode is reported as a bridge
    warning and returned as-is.

    Args:
        key: Name of the form field, used in the warning message.

        value: The submitted value, or list of values, to decode.

        element: The form control the value came from, used to attribute
            the warning to a DOM id.

    Returns:
        The decoded value(s), or the original value(s) where decoding
        was skipped or failed.
    """

    def decode_one(item: Any) -> Any:
        # Files and other non-string values are not JSON-decoded.
        if not isinstance(item, str):
            return item

        try:
            return json.loads(item)
        except json.JSONDecodeError as exc:
            report_bridge_warning(
                "bridge.form_field_decode_failed",
                f"Could not JSON-decode form field '{key}'; using raw value",
                "bridge.events.get_all_event_data",
                f"Field value: {item!r}",
                exception=exc,
                dom_id=element.id if hasattr(element, "id") else None,
                phase="event_dispatch",
            )
            return item

    if isinstance(value, list):
        return [decode_one(item) for item in value]

    return decode_one(value)


def apply_form_transforms(form: Any, form_values: dict[str, Any]) -> None:
    """Apply declared data-transform decodings to collected form values.

    Walks the form's controls and, for each field present in form_values
    whose element declares data-transform="json-decode", replaces the
    value with its JSON-decoded form in place. Each field name is
    processed at most once.

    Args:
        form: The form element whose controls declare the transforms.

        form_values: Mapping of collected form values, modified in place.
    """
    processed_names: set[str] = set()

    for element in form.elements:
        key = str(getattr(element, "name", "") or "")

        if not key or key in processed_names or key not in form_values:
            continue

        if element.getAttribute("data-transform") == "json-decode":
            form_values[key] = json_decode_form_value(
                key,
                form_values[key],
                element=element,
            )

        processed_names.add(key)


def build_payload_entries(
    form_values: dict[str, Any],
    event_data: dict[str, Any],
    argument_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Tag every collected value with its source, for router-side provenance.

    The router merges these by precedence (component arguments > event detail
    > form fields) and reports collisions, so all values are kept here.
    """
    entries: list[dict[str, Any]] = []
    for source, mapping in (
        ("form_field", form_values),
        ("event_detail", event_data),
        ("component_argument", argument_data),
    ):
        for key, value in mapping.items():
            entries.append(
                {
                    "name": str(key),
                    "value": value,
                    "source": source,
                    "source_detail": "",
                }
            )
    return entries


def unpack_event_bundle(bundle: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Split an event-data envelope into (merged values, provenance entries).

    Tolerates legacy plain-dict bundles (no provenance) for safety.
    """
    if isinstance(bundle, dict) and "values" in bundle and "payload" in bundle:
        return bundle.get("values") or {}, bundle.get("payload") or []
    return (bundle or {}, [])


def get_all_event_data(
    runtime: RuntimeAdapter,
    originator: Any,
    event: Any,
    submitter: Any,
    scope: Any = None,
) -> list:
    """Collect all relevant data for an event, including form data and arguments."""
    if scope is None:
        scope = runtime.context.document
    base_data: dict[str, Any] = {}

    # Phase 1: Get any custom event details
    if hasattr(event, "detail"):
        for key, value in js.Object.entries(event.detail):
            base_data[str(key)] = value

    # Phase 2: Get arguments from the originator and its parents
    argument_data: dict[str, Any] = {}

    arguments = get_attribute_recursively(
        originator, Component.DRAFTER_DATA_ARGUMENT_NAME
    )
    for i, arg in enumerate(reversed(arguments)):
        try:
            parsed = json.loads(arg)
        except Exception as e:
            report_bridge_error(
                "bridge.component_argument_corrupted",
                f"Could not parse component argument data ({i}); skipping it",
                "bridge.events.get_all_event_data",
                f"Argument value: {arg!r}",
                exception=e,
                dom_id=originator.id if hasattr(originator, "id") else None,
                phase="event_dispatch",
            )
            continue
        argument_data.update(parsed)

    # Phase 3: Get form data (scoped to this instance's shadow root)
    form = scope.querySelector("#" + DRAFTER_TAG_IDS["FORM"])

    if not form:
        merged = dict(base_data)
        merged.update(argument_data)
        return [
            runtime.promise_data(
                {
                    "values": merged,
                    "payload": build_payload_entries({}, base_data, argument_data),
                }
            )
        ]

    return process_form_data(
        runtime,
        form,
        submitter,
        base_data,
        argument_data,
    )


_PENDING_UPLOAD = object()


def _commit_uploaded_files(
    grouped: dict[str, Any], staging: dict[str, Any], key: str, index: int
):
    """Create a Promise.then callback for one uploaded file."""

    def commit(_result: Any) -> None:
        if key not in staging:
            raise RuntimeError(
                f"File upload for field {key!r} resolved without"
                "placing a value in the target mapping."
            )
        grouped[key][index] = staging[key]

    return commit


def collect_form_data(
    runtime: RuntimeAdapter,
    form: Any,
    submitter: Any,
) -> tuple[
    dict[str, list[Any]],
    set[str],
    list[Any],
]:
    """Collect raw form values, starting file uploads asynchronously.

    Builds a FormData snapshot of the form and groups every entry into a
    list per field name (pre-seeded with all multi-valued field names, so
    unchecked/empty multi-fields still appear). String values are stored
    directly; each file entry is stored as a pending-upload placeholder at
    its original position and replaced with the uploaded file data when
    its upload promise resolves. All fields are represented as lists until
    file uploads complete and cardinality normalization occurs (see
    `normalize_form_data`).

    Args:
        runtime: Runtime adapter used to create the FormData object,
            start file uploads, and chain their promises.
        form: The form element whose values are being collected.
        submitter: The element that submitted the form (passed to
            FormData so its name/value is included), or None.

    Returns:
        Tuple of (grouped, multiple_names, upload_promises), where
        `grouped` maps each field name to its list of raw values (file
        entries still pending until the promises resolve),
        `multiple_names` is the set of field names that may carry
        multiple values, and `upload_promises` is a list of promises that
        must all resolve before `grouped` contains only real values.
    """
    form_data = runtime.create_form_data(form, submitter)
    multiple_names = get_multiple_field_names(form)

    grouped: dict[str, list[Any]] = {name: [] for name in multiple_names}

    upload_promises: list[Any] = []

    for raw_key, value in form_data.entries():
        key = str(raw_key)
        values = grouped.setdefault(key, [])

        if isinstance(value, str):
            values.append(value)
            continue

        # Preserve the FormData entry's position, even when several uploads
        # for the same field finish out of order.
        index = len(values)
        values.append(_PENDING_UPLOAD)

        # handle_file_upload expects to write data[key]. Giving each
        # upload its own mapping prvents same-name files from overwriting each other.
        staging: dict[str, Any] = {}
        upload_promise = runtime.handle_file_upload(value, staging, key)

        commit = _commit_uploaded_files(grouped, staging, key, index)

        upload_promises.append(runtime.thenable(upload_promise, commit))
    return grouped, multiple_names, upload_promises


def ensure_uploads_resolved(
    grouped: dict[str, list[Any]],
) -> None:
    """Verify that no pending file-upload placeholders remain.

    collect_form_data stores a placeholder for each file entry until its
    upload promise commits the real data; this is called after all upload
    promises should have resolved, as a sanity check before the values
    are normalized.

    Args:
        grouped: Mapping from field name to its list of collected values.

    Raises:
        RuntimeError: If any field still contains an unresolved
            file-upload placeholder.
    """
    for key, values in grouped.items():
        for index, value in enumerate(values):
            if value is _PENDING_UPLOAD:
                raise RuntimeError(
                    f"File upload for field {key!r}, index {index}, has not resolved"
                )


def process_form_data(
    runtime: RuntimeAdapter,
    form: Any,
    submitter: Any,
    base_data: dict[str, Any],
    argument_data: dict[str, Any],
) -> list[Any]:
    """Collect and finalize a form's data into an event-data envelope.

    Collects the form's raw values (starting any file uploads), then —
    once all upload promises have resolved — normalizes cardinality,
    applies declared data-transform decodings, and merges values by
    precedence (component arguments > event detail > form fields). The
    result is wrapped as a {"values": ..., "payload": ...} envelope where
    payload carries per-value provenance entries.

    Args:
        runtime: Runtime adapter used to build the FormData object and
            chain the upload/finalization promises.

        form: The form element whose data is being collected.

        submitter: The element that submitted the form, or None.

        base_data: Values taken from the triggering event's detail.

        argument_data: Values taken from component argument attributes.

    Returns:
        Single-element list whose entry resolves to the envelope: the
        wrapped envelope itself when there are no uploads, otherwise a
        promise chain that finalizes after all uploads complete. Callers
        pass this list to runtime.finish_promises and read the envelope
        from the last resolved entry.
    """
    grouped, multiple_names, upload_promises = collect_form_data(
        runtime, form, submitter
    )
    single_checkbox_names = get_single_checkbox_names(form)

    def finalize(_result: Any = None) -> Any:
        ensure_uploads_resolved(grouped)

        form_values = normalize_form_data(
            grouped, multiple_names, single_checkbox_names
        )
        # Look for `data-transform` attributes to decode any special fields (e.g., JSON-encoded arguments)
        apply_form_transforms(form, form_values)
        # Merge by precedence: component arguments > event detail > form fields.
        data = dict(form_values)
        data.update(base_data)
        data.update(argument_data)
        # Return the promise itself (not wrapped in a list): when used as a
        # .then() callback, the thenable is flattened by the promise chain,
        # and callers expect files_and_data[-1] to be the envelope dict.
        return runtime.promise_data(
            {
                "values": data,
                "payload": build_payload_entries(form_values, base_data, argument_data),
            }
        )

    if not upload_promises:
        return [finalize()]

    return [runtime.finish_promises(upload_promises, finalize)]
