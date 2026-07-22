from typing import Any, Optional
from drafter.monitor.bus import EventBus
from drafter.client_server.client_server import ClientServer

# The "current" server: the one being configured/executed right now. Route
# decorators and start_server() resolve through this during code execution, and
# request handlers set it around dispatch (see bridger.handle_visit) so runtime
# get_main_server() calls resolve to the correct instance.
MAIN_SERVER: Optional[ClientServer] = None

# Registry of all live servers, keyed by instance key: the instance_id passed
# to configure_instance() when given, otherwise the root_element_id. Iframe
# embedded instances all use the same (default) root id in their own documents,
# so the root id alone cannot distinguish them within the shared interpreter.
_SERVER_REGISTRY: dict[str, ClientServer] = {}

# Context handed over by the most recent configure_instance() call, consumed by
# the next run_client_bridge(). Execution of configure -> student code is
# serialized by the JS execution queue, so a single pending slot is safe.
# Holds "window" (the JS window this instance renders into, e.g. an iframe's
# contentWindow), "instance_id" (the registry key), and "instance_root" (the
# instance's virtual-filesystem folder).
_PENDING_INSTANCE_CONTEXT: Optional[dict[str, Any]] = None

# Virtual-filesystem folder of the instance whose code is currently executing
# (e.g. "/instances/demo-1"). Relative file paths in student code resolve here
# so instances sharing one interpreter don't read or write each other's files.
# Kept in sync by configure_instance() (initial run) and set_main_server()
# (event dispatch); None means the interpreter-wide default (single instance).
_CURRENT_INSTANCE_ROOT: Optional[str] = None


def set_main_server(server: Optional[ClientServer]):
    """Set the global "current" server reference.

    Also points the current instance-root at the server's filesystem folder so
    file operations triggered by this server's code resolve into its subtree.

    Args:
        server: Server instance to register globally (or None to clear).
    """
    global MAIN_SERVER, _CURRENT_INSTANCE_ROOT
    MAIN_SERVER = server
    if server is not None:
        _CURRENT_INSTANCE_ROOT = getattr(server, "instance_root", None)


def get_current_instance_root() -> Optional[str]:
    """The virtual-filesystem folder of the currently executing instance."""
    return _CURRENT_INSTANCE_ROOT


def set_current_instance_root(instance_root: Optional[str]) -> None:
    """Point relative file resolution at a specific instance folder."""
    global _CURRENT_INSTANCE_ROOT
    _CURRENT_INSTANCE_ROOT = instance_root


def get_main_server() -> ClientServer:
    """Return the current server, creating a default one if missing.

    Returns:
        ClientServer: The current server instance.
    """
    global MAIN_SERVER
    if MAIN_SERVER is None:
        MAIN_SERVER = ClientServer("MAIN_SERVER")
    return MAIN_SERVER


def register_server(instance_key: str, server: ClientServer) -> None:
    """Register a server under its instance key and make it current.

    Args:
        instance_key: The instance's unique key (instance_id, or the
            root_element_id when no explicit instance_id was configured).
        server: The server driving that instance.
    """
    _SERVER_REGISTRY[instance_key] = server
    set_main_server(server)


def get_server_for_root(instance_key: str) -> Optional[ClientServer]:
    """Look up the server registered for a given instance key.

    Args:
        instance_key: The instance's key (instance_id or root_element_id).

    Returns:
        The registered server, or None if no instance uses that key.
    """
    return _SERVER_REGISTRY.get(instance_key)


def reset_server_for_root(instance_key: str) -> None:
    """Forget the server registered for a given instance key.

    Clears the current-server pointer too if it referenced this instance, so a
    stale server is never left as the default.

    Args:
        instance_key: The instance's key (instance_id or root_element_id).
    """
    global MAIN_SERVER
    server = _SERVER_REGISTRY.pop(instance_key, None)
    if server is not None and MAIN_SERVER is server:
        MAIN_SERVER = None


def consume_pending_instance_context() -> Optional[dict[str, Any]]:
    """Take (and clear) the context left by the last configure_instance() call.

    Called by run_client_bridge() when an instance starts, so its ClientBridge
    targets the window configure_instance() was given. Returns None on the
    single-instance path, where configure_instance() is never called.
    """
    global _PENDING_INSTANCE_CONTEXT
    pending = _PENDING_INSTANCE_CONTEXT
    _PENDING_INSTANCE_CONTEXT = None
    return pending


def get_main_event_bus() -> EventBus:
    """Return the event bus associated with the current server.

    Returns:
        EventBus: Event bus of the current server.
    """
    return get_main_server().event_bus


def configure_instance(
    root_element_id: str,
    use_shadow_dom: Optional[bool] = None,
    js_window: Any = None,
    instance_id: Optional[str] = None,
    instance_root: Optional[str] = None,
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
        js_window: The JS window this instance renders into (an iframe's
            contentWindow for embedded instances). None targets the global
            window as before.
        instance_id: Unique registry key for this instance. Required when
            several instances share a root_element_id (each in its own iframe
            document); defaults to root_element_id otherwise.
        instance_root: Virtual-filesystem folder for this instance (e.g.
            "/instances/demo-1"). Relative file paths in the instance's code
            resolve here. None keeps the interpreter-wide default.
    """
    from drafter.configuration import get_system_configuration

    global _PENDING_INSTANCE_CONTEXT
    _PENDING_INSTANCE_CONTEXT = {
        "window": js_window,
        "instance_id": instance_id or root_element_id,
        "instance_root": instance_root,
    }

    # Clear the current-server slot so this instance's first @route (which runs
    # before its start_server()) creates a *fresh* server instead of registering
    # onto the previous instance's leftover one.
    set_main_server(None)
    # The instance's code is about to execute; import-time file operations must
    # already resolve into its folder (set_main_server(None) doesn't sync this).
    set_current_instance_root(instance_root)

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
