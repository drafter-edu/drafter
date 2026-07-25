"""
ClientBridge: the unified bridge between the Python application and the browser DOM.

Handles site setup, DOM updates, navigation, event handling, request/response
management, channel content, redirect detection, history, hotkeys, and telemetry.
Runtime-specific differences (Skulpt vs Pyodide) are delegated to a RuntimeAdapter.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from drafter.bridge.context import DomContext
from drafter.bridge.dom import (
    set_favicon,
    swap_debug_mode,
    update_subtle_debug_entry,
)
from drafter.bridge.error_handling import (
    raise_bridge_system_error,
    report_bridge_error,
)
from drafter.bridge.events import EventManager
from drafter.bridge.hooks import ServerHooks
from drafter.bridge.log import console_log, debug_log
from drafter.bridge.navigation import NavigationController
from drafter.bridge.persistence import evict_key
from drafter.bridge.runtime import RuntimeAdapter, create_runtime
from drafter.bridge.site_renderer import SiteRenderer
from drafter.bridge.snapshot import (
    deserialize_state_snapshot,
    serialize_state_snapshot,
)
from drafter.config.client_server import ClientServerConfiguration
from drafter.data.details.config import UpdatedConfigurationEvent
from drafter.data.details.state import UpdatedStateEvent
from drafter.data.request import Request
from drafter.data.response import Response
from drafter.data.telemetry import TelemetryRecord
from drafter.monitor.audit import log_record
from drafter.site.initial_site_data import InitialSiteData
from drafter.site.site import (
    DRAFTER_TAG_IDS,
)
from drafter.styling.themes import get_theme_system


@dataclass
class ClientBridge:
    """Coordinates the browser side of a running Drafter instance.

    Owns the DOM rendering (SiteRenderer), navigation (NavigationController),
    event wiring (EventManager), and the optional debug panel for one
    instance, delegating runtime-specific operations to a RuntimeAdapter.
    Constructed with only a configuration and an optional DomContext; the
    collaborators are built from those.

    Attributes:
        site_renderer: Renders and updates this instance's DOM.

        navigator: Initiates requests and manages redirects and history.

        configuration: The client/server configuration for this instance.

        debug_panel: The JS debug panel component, once set up (None before
            setup or if setup failed).

        runtime: Adapter for runtime-specific (Skulpt vs Pyodide) operations.

        site_title: The site's title, as last set by set_site_title.

        context: The DomContext (window/document) this instance renders into.

        events: Manages DOM event listeners and hotkeys for this instance.

        hooks: Server-facing operations injected by the composition root
            via setup_events (None until then). The bridge reaches the
            server only through these, never through a global lookup.
    """

    site_renderer: SiteRenderer
    navigator: NavigationController
    configuration: ClientServerConfiguration = field(init=False)
    debug_panel: Any | None = None
    runtime: RuntimeAdapter = field(default_factory=create_runtime)
    site_title: str = "Default Title"
    hooks: ServerHooks | None = None

    def __init__(
        self,
        configuration: ClientServerConfiguration,
        context: DomContext | None = None,
    ):
        self.context = context if context is not None else DomContext.default()
        self.runtime = create_runtime(self.context)
        self.configuration = configuration
        self.site_renderer = SiteRenderer(
            self.runtime, configuration.root_element_id, configuration.root_element_id
        )
        self.navigator = NavigationController(self.runtime)
        self.events = EventManager(self.runtime)
        self.debug_panel = None
        self.hooks = None
        # Re-entrancy guard for _handle_debug_events: reporting a debug-panel
        # failure publishes an error event on the same bus this bridge
        # subscribes to, which would otherwise re-enter the same failing
        # panel forever (an unbounded synchronous recursion that freezes the
        # tab). While True, incoming events are not forwarded to the panel.
        self._forwarding_debug_event = False

    def setup_site(self, initial_site_data: InitialSiteData) -> None:
        """Build the initial site DOM and prepare instance-scoped machinery.

        Sets the site title, has the SiteRenderer construct the site frame
        from the initial site data, updates the subtle production debug-entry
        button's visibility, scopes the EventManager's element lookups to the
        renderer's scope (shadow root or root element) so concurrent
        instances never resolve each other's elements, and sets up the debug
        panel.

        Args:
            initial_site_data: The rendered initial site (HTML, title,
                assets, and flags) produced by the server's render phase.
        """
        self.set_site_title(initial_site_data.site_title)
        if initial_site_data.favicon:
            self.set_site_favicon(initial_site_data.favicon)
        self.site_renderer.setup(initial_site_data)
        update_subtle_debug_entry(
            self.site_renderer.get_scope(),
            self.configuration.in_debug_mode,
            self.configuration.enable_subtle_debug_entry,
        )
        # Scope this instance's event lookups (BODY/FORM) to the same node the
        # renderer rendered into (its shadow root, when shadow DOM is on), so
        # concurrent instances never resolve each other's elements.
        self.events.set_scope(self.site_renderer.scope)
        self._setup_debug_menu()

    def setup_events(self, hooks: ServerHooks) -> None:
        """Install the injected server hooks and register DOM event handlers.

        Wires the hooks' visit callback into the NavigationController,
        registers the Drafter custom events (toggle-frame, toggle-debug-mode,
        evict-persistent, navigate, replay, save/load-state, set-theme) and
        the browser popstate event, binds the "Q" hotkey to debug-mode
        toggling, and mounts the subtle production debug-entry button. Every
        registered handler runs behind hooks.activate, which pins this
        instance's server as "current" so telemetry raised inside a handler
        routes to this instance's event bus.

        Args:
            hooks: The server-facing operations assembled by the composition
                root (bridger.build_server_hooks) for this instance.
        """
        self.hooks = hooks
        self.navigator.set_navigation_func(hooks.visit)
        self.events.setup_events(
            {
                "drafter-toggle-frame": lambda event: hooks.toggle_frame(),
                "drafter-toggle-debug-mode": lambda event: hooks.toggle_debug_mode(),
                "drafter-evict-persistent": lambda event: self.evict_persistent(event),
                "drafter-navigate": lambda event: self.navigator.goto(event.detail),
                "drafter-replay-route": lambda event: self.navigator.replay_last(),
                "drafter-replay-request": lambda event: self.replay_request(event),
                "drafter-save-state": lambda event: self.save_state_snapshot(event),
                "drafter-load-state": lambda event: self.load_state_snapshot(event),
                "drafter-set-theme": lambda event: self.set_site_theme(event),
                "popstate": self.navigator.handle_popstate,
            },
            {
                "Q": hooks.toggle_debug_mode,
            },
            activate=hooks.activate,
        )
        # The subtle production debug-entry button is part of the site frame
        # (injected once at setup, outside the re-rendered body), so a single
        # direct binding here covers the instance's lifetime.
        self.events.mount_subtle_debug_entry(hooks.toggle_debug_mode)

    def start(self):
        """
        Load the initial request.
        """
        self.navigator.do_initial_request()

    def evict_persistent(self, event) -> None:
        """Evict a persisted component by key (from the debug panel UI)."""
        key = getattr(event, "detail", None)
        if not key:
            return
        parking_area = self.site_renderer.get_parking_area()
        if parking_area is not None:
            evict_key(parking_area, str(key))

    def replay_request(self, event) -> None:
        """Replay a specific past request (from the debug history's Revisit).

        The event detail carries `{request_id}`; the actual Request object
        is looked up Python-side (telemetry only has a repr of its kwargs).
        """
        detail = getattr(event, "detail", None)
        request_id = getattr(detail, "request_id", None)
        if request_id is None:
            report_bridge_error(
                "client.replay_request_missing_id",
                "Replay request event arrived without a request_id",
                "bridge.client_bridge.replay_request",
                f"Event detail: {repr(detail)}",
                phase="navigation",
            )
            return
        self.navigator.replay_by_id(int(request_id))

    def _require_hooks(self) -> ServerHooks:
        """Return the injected ServerHooks, failing loudly when absent.

        The handlers that call this are only wired up by setup_events,
        which installs the hooks first, so a None here is a wiring bug in
        the composition root rather than a user error.
        """
        if self.hooks is None:
            raise RuntimeError(
                "ClientBridge server hooks are not installed; setup_events "
                "must run before server-facing handlers are invoked."
            )
        return self.hooks

    ### State Snapshots (debug menu Save/Load)

    def save_state_snapshot(self, event) -> None:
        """Capture the current state + route invocation as a snapshot event.

        Responds to the debug UI's ``drafter-save-state`` window event (its
        detail carries `{reason, slot}`). The snapshot travels back to the
        JS SaveLoadManager as StateSnapshot telemetry, which stores it in
        localStorage or downloads it as a file.
        """
        detail = getattr(event, "detail", None)
        reason = str(getattr(detail, "reason", None) or "save")
        slot = str(getattr(detail, "slot", None) or "quick")
        last = self.navigator.last_request
        route = last.url if last else "index"
        kwargs = dict(last.kwargs) if last else {}
        state = self._require_hooks().get_state()
        snapshot = serialize_state_snapshot(
            state, route, kwargs, reason, slot, self.site_title
        )
        if snapshot is not None:
            log_record(
                snapshot,
                "bridge.client_bridge.save_state_snapshot",
                route=route,
                request_id=last.id if last else None,
            )

    def load_state_snapshot(self, event) -> None:
        """Restore a previously saved snapshot and replay its route.

        Responds to the debug UI's ``drafter-load-state`` window event (its
        detail carries `{state_json, route, kwargs_json}`). The state is
        rebuilt from plain data against the running app's state class,
        restored first, and then the route is re-invoked, because argument
        preparation reads the current state.
        """
        detail = getattr(event, "detail", None)
        state_json = getattr(detail, "state_json", None)
        route = str(getattr(detail, "route", None) or "index")
        kwargs_json = str(getattr(detail, "kwargs_json", None) or "{}")
        if not state_json:
            report_bridge_error(
                "client.load_snapshot_missing_payload",
                "Load state event arrived without a saved state payload",
                "bridge.client_bridge.load_state_snapshot",
                f"Event detail: {repr(detail)}",
                phase="event_dispatch",
            )
            return
        hooks = self._require_hooks()
        try:
            restored = deserialize_state_snapshot(str(state_json), hooks.get_state())
        except Exception as e:
            report_bridge_error(
                "client.load_snapshot_failed",
                "Could not load the saved state; it may have been saved under a "
                "different version of your code",
                "bridge.client_bridge.load_state_snapshot",
                f"Route: {route}",
                exception=e,
                route=route,
                phase="event_dispatch",
            )
            return
        try:
            kwargs = json.loads(kwargs_json)
        except Exception:
            kwargs = {}
        # Restore the state BEFORE replaying the route: argument preparation
        # reads state.current when invoking the route handler.
        hooks.set_state(restored)
        log_record(
            UpdatedStateEvent.from_state(restored),
            "bridge.client_bridge.load_state_snapshot",
            route=route,
        )
        self.navigator.goto(route, kwargs, action="system")

    ### Theme Switching (debug menu View > Switch Theme)

    def set_site_theme(self, event) -> None:
        """Change the site theme in response to a ``drafter-set-theme`` event.

        Mirrors the frame toggle's flow: the event triggers a server
        reconfigure, whose UpdatedConfiguration telemetry loops back into
        handle_server_event, which refreshes the connected theme stylesheets
        in place — no page reload.

        Args:
            event: The window CustomEvent; its detail is the theme name.
        """
        theme = str(getattr(event, "detail", None) or "")
        if not theme:
            report_bridge_error(
                "client.set_theme_missing_name",
                "Set theme event arrived without a theme name",
                "bridge.client_bridge.set_site_theme",
                f"Event detail: {repr(getattr(event, 'detail', None))}",
                phase="event_dispatch",
            )
            return
        theme_system = get_theme_system()
        if theme != "none" and not theme_system.is_valid_theme(theme):
            report_bridge_error(
                "client.set_theme_unknown",
                theme_system.suggest_mistake(theme),
                "bridge.client_bridge.set_site_theme",
                f"Requested theme: {theme}",
                phase="event_dispatch",
            )
            return
        self._require_hooks().set_theme(theme)

    def _refresh_site_theme(self) -> None:
        """Re-render the theme stylesheets for the current configuration.

        Site.render() is a pure data computation (it never touches the DOM),
        so it is safe to call here just to learn the new cascade-ordered CSS
        list; the SiteRenderer then swaps only the stale stylesheet links.
        """
        try:
            site_data = self._require_hooks().render_site()
            self.site_renderer.refresh_theme_css(site_data.additional_css)
        except Exception as e:
            report_bridge_error(
                "client.theme_refresh_failed",
                "Could not apply the new theme to the page",
                "bridge.client_bridge._refresh_site_theme",
                f"Theme: {self.configuration.theme}",
                exception=e,
                phase="event_dispatch",
            )

    ### Debug Panel

    def _setup_debug_menu(self):
        debug_log("client.setup_debug_menu")
        try:
            self.debug_panel = self.runtime.create_debug_panel(
                DRAFTER_TAG_IDS["DEBUG"], self, self.site_renderer.scope
            )
        except Exception as e:
            raise_bridge_system_error(
                "client.setup_debug_menu_failed",
                "Failed to set up debug panel",
                "bridge.client_bridge._setup_debug_menu",
                f"Container id: {DRAFTER_TAG_IDS['DEBUG']}",
                exception=e,
                phase="setup",
            )

    def _handle_debug_events(self, event: dict) -> bool:
        if self._forwarding_debug_event:
            # This event was published while we were already forwarding one
            # to the debug panel (i.e. while reporting that the forward
            # failed). Forwarding it too would re-enter the same failing
            # panel and recurse without bound, so drop it here; the caller
            # logs unhandled events to the console.
            return False
        self._forwarding_debug_event = True
        try:
            try:
                js_event = self.runtime.convert_to_js(event)
            except Exception as e:
                report_bridge_error(
                    "client.convert_event_to_js",
                    f"Error converting event to JS: {repr(e)}",
                    "bridge.client_bridge.handle_server_event",
                    f"Exception: {repr(e)}",
                    exception=e,
                    phase="event_dispatch",
                )
                return False
            if self.debug_panel:
                try:
                    handled = self.debug_panel.handleEvent(js_event)
                    return handled
                except Exception as e:
                    raise_bridge_system_error(
                        "client.handle_debug_event_failed",
                        "Failed to handle debug panel event",
                        "bridge.client_bridge._handle_debug_events",
                        f"Event: {repr(event)}",
                        exception=e,
                        phase="event_dispatch",
                    )
            else:
                raise_bridge_system_error(
                    "client.no_debug_panel",
                    "No debug panel is available to handle telemetry event",
                    "bridge.client_bridge._handle_debug_events",
                    f"Event: {repr(event)}",
                    phase="event_dispatch",
                )
            return False
        finally:
            self._forwarding_debug_event = False

    def teardown(self) -> None:
        """Disconnect this bridge from the browser so a successor can replace it.

        Removes the EventManager's window/document listeners and drops the
        debug panel reference. Called when the instance is being discarded
        (reset before an editor-driven re-run, or embed detach); without it,
        the old bridge's global listeners keep routing browser events into a
        bridge whose DOM no longer exists.
        """
        try:
            self.events.teardown()
        except Exception as e:
            report_bridge_error(
                "client.bridge_teardown_failed",
                "Failed to remove a torn-down bridge's event listeners",
                "bridge.client_bridge.teardown",
                f"Exception: {repr(e)}",
                exception=e,
                phase="setup",
            )
        self.debug_panel = None

    def _notify_debug_panel(self, response_url: str):
        if self.debug_panel:
            self.debug_panel.setRoute(response_url)

    ### Response Handling

    def handle_response(
        self, response: Response, callback: Callable[[Request], Response]
    ) -> bool:
        """Commit a server Response to the DOM (the Committing Phase).

        Clears the previous page's page-specific content, applies the
        response's "before" channel, refreshes the navigation function and
        the debug panel's route, and updates the site body. When the DOM was
        updated, re-mounts navigation handlers and (for full page loads)
        dispatches the page-loaded event. Finally applies the "after"
        channel and, if the payload is a redirect, follows it via the
        NavigationController.

        Args:
            response: The Response produced by visiting a route.
            callback: The visit function to use for subsequent navigation
                (including any redirect this response triggers).

        Returns:
            True if the site DOM was updated (and event handlers were
            re-registered), False otherwise.
        """
        self.site_renderer.remove_page_specific_content()
        self.site_renderer.apply_before_channel(response)
        self.navigator.set_navigation_func(callback)
        self._notify_debug_panel(response.url)
        updated = self.site_renderer.update_site(response)
        if updated:
            self.site_renderer.apply_page_transition(
                self.configuration.page_transition,
                self.configuration.page_transition_duration,
            )
            self.events.mount_navigation(self.navigator.navigate)
            # TODO: Improve this check for a full page load
            if not response.target or response.target.is_page_load:
                self.events.dispatch_page_loaded(
                    route=response.url,
                    request_id=response.request_id,
                    response_id=response.id,
                )
        self.site_renderer.apply_after_channel(response)
        if response.payload.is_redirect():
            self.navigator.handle_redirect(response, callback)
        return updated

    ### Event Handling
    def handle_server_event(self, event_data: TelemetryRecord) -> bool:
        """Process a telemetry event published by the server.

        Configuration-update events are applied directly: "framed" toggles
        the site frame, while "in_debug_mode" and "enable_subtle_debug_entry"
        update the configuration and refresh the debug CSS and subtle
        debug-entry button. Every event (including configuration updates) is
        then forwarded to the debug panel; events the panel does not handle
        are logged to the console.

        Args:
            event_data: The telemetry record published on the server's
                event bus.

        Returns:
            True if the debug panel handled the event, False otherwise
            (including when the event could not be converted to JSON).
        """
        try:
            event = event_data.to_json()
            debug_log("client.handle_event", event)
        except Exception as e:
            report_bridge_error(
                "client.convert_event_to_json",
                f"Error converting event to JSON: {repr(e)}",
                "bridge.client_bridge.handle_server_event",
                f"Exception: {repr(e)}",
                exception=e,
                phase="event_dispatch",
            )
            return False
        if event["kind"] == UpdatedConfigurationEvent.kind:
            if event.get("key") == "framed":
                self.site_renderer.toggle_frame()
            elif event.get("key") == "in_debug_mode":
                self.configuration.in_debug_mode = bool(event.get("value"))
                swap_debug_mode(self.context.document)
                update_subtle_debug_entry(
                    self.site_renderer.get_scope(),
                    self.configuration.in_debug_mode,
                    self.configuration.enable_subtle_debug_entry,
                )
            elif event.get("key") == "enable_subtle_debug_entry":
                self.configuration.enable_subtle_debug_entry = bool(event.get("value"))
                update_subtle_debug_entry(
                    self.site_renderer.get_scope(),
                    self.configuration.in_debug_mode,
                    self.configuration.enable_subtle_debug_entry,
                )
            elif event.get("key") == "favicon":
                self.configuration.favicon = str(event.get("value"))
                self.set_site_favicon(self.configuration.favicon)
            elif event.get("key") == "theme":
                self.configuration.theme = str(event.get("value"))
                self._refresh_site_theme()
            elif event.get("key") == "page_transition":
                self.configuration.page_transition = str(event.get("value"))
            elif event.get("key") == "page_transition_duration":
                self.configuration.page_transition_duration = float(
                    event.get("value") or 0.0
                )
            else:
                report_bridge_error(
                    "client.unhandled_config_update",
                    "Unhandled configuration update event",
                    "bridge.client_bridge.handle_server_event",
                    f"Event payload: {repr(event)}",
                    phase="event_dispatch",
                )
        handled = self._handle_debug_events(event)

        # Any unhandled events get logged to the console for now
        if not handled:
            console_log(event)

        return handled

    ### Specialized Helpers

    def set_site_title(self, title: str) -> None:
        """Set the site title, updating the document and debug panel.

        The browser document's <title> is only changed when this instance is
        the primary one (rendering into the default root id); secondary
        instances sharing a document must not fight over it. The debug
        panel's header title is always updated when the panel exists.

        Args:
            title: The new site title.
        """
        self.site_title = title
        # Only the primary instance (the default root) owns its document's
        # <title>; secondary instances sharing a document must not fight over
        # it. Embedded instances each own their iframe's document, so their
        # (default-root) titles never collide.
        if self.site_renderer.root_id == DRAFTER_TAG_IDS["ROOT"]:
            self.context.document.title = title
        if self.debug_panel:
            self.debug_panel.setHeaderTitle(title)
        # debug_log("client.set_title", title)

    def set_site_favicon(self, favicon: str) -> None:
        """Set the browser tab icon for this instance's document.

        Like the document `<title>`, the favicon belongs to the document as
        a whole, so only the primary instance (rendering into the default
        root id) may change it; secondary instances sharing a document must
        not fight over it.

        Args:
            favicon: URL of the icon image (relative path, absolute URL, or
                data URI).
        """
        if self.site_renderer.root_id == DRAFTER_TAG_IDS["ROOT"]:
            set_favicon(self.context.document, favicon)
