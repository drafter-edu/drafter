from collections import Counter
import json
from operator import mul
import time
from dataclasses import dataclass, field
from typing import Any, Callable
from drafter.bridge.runtime import RuntimeAdapter
from drafter.data.request import Request
from drafter.bridge.log import debug_log
from drafter.bridge.error_handling import (
    raise_bridge_system_error,
    report_bridge_error,
    report_bridge_warning,
)
from drafter.components.page_content import Component
from drafter.site.site import DRAFTER_TAG_IDS
from drafter.bridge.dom import (
    get_attribute_recursively,
)
import js

DOUBLE_PRESS_THRESHOLD = 600  # milliseconds
DRAFTER_PAGE_LOADED_EVENT = "drafter-page-loaded"


@dataclass
class EventManager:
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
        # The node inner-frame lookups (BODY/FORM) are scoped to. Defaults to the
        # global document (single-instance); set to the instance's shadow root by
        # set_scope() so concurrent instances don't find each other's elements.
        self.scope: Any = js.document

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
                            data = files_and_data[-1] if files_and_data else {}
                            request = Request(
                                action=event_name,
                                url=route,
                                kwargs=data,
                                event={},  # TODO: Populate this with useful event info
                                dom_id=dom_id or "",
                                button_pressed=target_element,
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

    def mount_navigation(self, do_navigation: Callable):
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
                    data = files_and_data[-1] if files_and_data else {}
                    request = Request(
                        action="link",
                        url=name,
                        kwargs=data,
                        event={},  # TODO: Populate this with useful event info
                        dom_id=dom_id or "",
                        button_pressed=nearest_nav_link if not is_anchor else "",
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
                url = js.location.href
            # Build and dispatch navigation event
            incomplete_data = get_all_event_data(
                self.runtime, event.target, event, submitter, self.scope
            )

            def finish_form_navigation(data):
                request = Request(
                    action="form",
                    url=url,
                    kwargs=data,
                    event={},  # TODO: Populate this with useful event info
                    dom_id=dom_id or "",
                    button_pressed=submitter if submitter else "",
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

    ### Global Event Handler Registration
    def setup_events(
        self,
        event_handlers: dict[str, Callable[[Any], Any]],
        key_handlers: dict[str, Callable[[], None]],
    ) -> None:
        debug_log("client.setup_events")

        # Global events
        for event_name, handler in event_handlers.items():
            self._register_event(event_name, handler)

        # Keyboard events
        for key_combo, handler in key_handlers.items():
            self._register_hotkey(key_combo, handler)

    def dispatch_page_loaded(
        self, route: str, request_id: int, response_id: int
    ) -> None:
        detail = {
            "route": route,
            "requestId": request_id,
            "responseId": response_id,
        }
        event = self.runtime.create_custom_event(DRAFTER_PAGE_LOADED_EVENT, detail)
        self.runtime.dispatch_window_event(event)
        debug_log("client.page_loaded_event_dispatched", detail)

    def _register_event(self, event_name: str, handler: Callable[[Any], Any]) -> None:
        if self.listeners.get(event_name):
            js.removeEventListener(event_name, self.listeners[event_name])
            self.runtime.cleanup_event_handler(self.listeners[event_name])
        wrapped_handler = self.runtime.wrap_event_handler(handler)
        js.addEventListener(event_name, wrapped_handler)
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
            js.document.addEventListener("keydown", wrapped_handler)
            self.hotkey_listener_ready = True
            debug_log("client.hotkey_listener_registered")


def get_single_checkbox_names(form: Any) -> set[str]:
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


def get_all_event_data(
    runtime: RuntimeAdapter,
    originator: Any,
    event: Any,
    submitter: Any,
    scope: Any = js.document,
) -> list:
    """Collect all relevant data for an event, including form data and arguments."""
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
        base_data.update(argument_data)
        return [runtime.promise_data(base_data)]

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
    """
    Collect raw form values.

    All fields are represented as lists until file uploads complete
    and cardinality normalization occurs.

    Args:
        runtime (RuntimeAdapter): _description_
        form (Any): _description_
        submitter (Any): _description_

    Returns:
        tuple[ dict[str, list[Any]], set[str], list[Any], ]: _description_
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
        data = dict(base_data)
        data.update(form_values)
        data.update(argument_data)
        # Return the promise itself (not wrapped in a list): when used as a
        # .then() callback, the thenable is flattened by the promise chain,
        # and callers expect files_and_data[-1] to be the data dict.
        return runtime.promise_data(data)

    if not upload_promises:
        return [finalize()]

    return [runtime.finish_promises(upload_promises, finalize)]
