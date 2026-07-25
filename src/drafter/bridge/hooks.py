"""
ServerHooks: the server-facing operations injected into a ClientBridge.

The bridge never looks up "the server" itself. The composition root
(bridger.run_client_bridge) closes over its ClientServer instance and hands
the bridge these callables instead, keeping the bridge ignorant of the
server class and the global current-server pointer. Each server-touching
hook is expected to pin its instance as the current server (via
set_main_server) before acting, so bus-routed telemetry (log_record,
report_bridge_error) lands on the right instance's event bus even when
several instances share one interpreter.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from drafter.data.request import Request
from drafter.data.response import Response
from drafter.site.initial_site_data import InitialSiteData


@dataclass
class ServerHooks:
    """Server-facing callables the composition root injects into a bridge.

    Built by bridger.build_server_hooks, which wraps every server-touching
    operation so it pins its own instance as the current server first
    (the same discipline handle_visit and handle_toggle_frame follow).

    Attributes:
        activate: Pins this instance's server as the "current" server.
            The EventManager runs it before every registered window event
            and hotkey handler, so telemetry raised anywhere inside a
            handler routes to this instance's event bus.

        visit: Performs a full visit for a Request and returns its
            Response; used for all navigation.

        toggle_frame: Flips the site frame configuration.

        toggle_debug_mode: Flips debug mode.

        set_theme: Reconfigures the server with the given theme name.

        get_state: Returns the server's current application state.

        set_state: Replaces the server's current application state.

        render_site: Renders the server's site data (a pure computation;
            it never touches the DOM), e.g. to learn the current
            cascade-ordered stylesheet list after a theme change.
    """

    activate: Callable[[], None]
    visit: Callable[[Request], Response]
    toggle_frame: Callable[[], None]
    toggle_debug_mode: Callable[[], None]
    set_theme: Callable[[str], None]
    get_state: Callable[[], Any]
    set_state: Callable[[Any], None]
    render_site: Callable[[], InitialSiteData]
