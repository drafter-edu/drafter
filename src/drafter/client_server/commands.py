from typing import Optional
from drafter.monitor.bus import EventBus
from drafter.client_server.client_server import ClientServer

# The "current" server: the one being configured/executed right now. Route
# decorators and start_server() resolve through this during code execution, and
# request handlers set it around dispatch (see bridger.handle_visit) so runtime
# get_main_server() calls resolve to the correct instance.
MAIN_SERVER: Optional[ClientServer] = None

# Registry of all live servers, keyed by their root_element_id. This lets
# multiple concurrent Drafter instances coexist on one page: each app registers
# under its unique root id and can be looked up or reset independently.
_SERVER_REGISTRY: dict[str, ClientServer] = {}


def set_main_server(server: Optional[ClientServer]):
    """Set the global "current" server reference.

    Args:
        server: Server instance to register globally (or None to clear).
    """
    global MAIN_SERVER
    MAIN_SERVER = server


def get_main_server() -> ClientServer:
    """Return the current server, creating a default one if missing.

    Returns:
        ClientServer: The current server instance.
    """
    global MAIN_SERVER
    if MAIN_SERVER is None:
        MAIN_SERVER = ClientServer("MAIN_SERVER")
    return MAIN_SERVER


def register_server(root_id: str, server: ClientServer) -> None:
    """Register a server under its root element id and make it current.

    Args:
        root_id: The instance's unique root_element_id.
        server: The server driving that instance.
    """
    _SERVER_REGISTRY[root_id] = server
    set_main_server(server)


def get_server_for_root(root_id: str) -> Optional[ClientServer]:
    """Look up the server registered for a given root element id.

    Args:
        root_id: The instance's root_element_id.

    Returns:
        The registered server, or None if no instance uses that root.
    """
    return _SERVER_REGISTRY.get(root_id)


def reset_server_for_root(root_id: str) -> None:
    """Forget the server registered for a given root element id.

    Clears the current-server pointer too if it referenced this instance, so a
    stale server is never left as the default.

    Args:
        root_id: The instance's root_element_id.
    """
    global MAIN_SERVER
    server = _SERVER_REGISTRY.pop(root_id, None)
    if server is not None and MAIN_SERVER is server:
        MAIN_SERVER = None


def get_main_event_bus() -> EventBus:
    """Return the event bus associated with the current server.

    Returns:
        EventBus: Event bus of the current server.
    """
    return get_main_server().event_bus


def configure_instance(
    root_element_id: str, use_shadow_dom: Optional[bool] = None
) -> None:
    """Point the next start_server() at a specific root element and DOM mode.

    Called by the JS bootstrap immediately before executing an instance's code so
    that when the student's start_server() triggers do_configuration(), it renders
    into this instance's own root (and, with shadow DOM, its own isolated subtree).
    This is what lets several concurrent instances coexist on one page.

    Only invoked when a root is explicitly requested (the multi-instance path); the
    single-instance back-compat path never calls this, preserving config/env
    defaults exactly.

    Args:
        root_element_id: The unique id of this instance's root <div>.
        use_shadow_dom: Whether to isolate this instance in a shadow root. If
            None, the existing configuration value is left unchanged.
    """
    from drafter.configuration import get_system_configuration

    # Clear the current-server slot so this instance's first @route (which runs
    # before its start_server()) creates a *fresh* server instead of registering
    # onto the previous instance's leftover one.
    set_main_server(None)

    system = get_system_configuration()
    system.client_server.root_element_id = root_element_id
    if use_shadow_dom is not None:
        system.client_server.use_shadow_dom = use_shadow_dom

    # These per-app content lists live on the shared system config and are
    # *appended* to by add_website_css()/add_website_js()/etc. Without a reset,
    # one instance's injected CSS/JS would accumulate and leak into every
    # instance configured after it. Give each instance a clean slate.
    for field_name in (
        "additional_css_content",
        "additional_style_content",
        "additional_js_content",
        "additional_script_content",
        "additional_header_content",
    ):
        setattr(system.client_server, field_name, [])
