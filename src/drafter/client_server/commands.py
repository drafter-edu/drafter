from typing import Optional
from drafter.monitor.bus import EventBus
from drafter.client_server.client_server import ClientServer

MAIN_SERVER: Optional[ClientServer] = None


def set_main_server(server: ClientServer):
    """Set the global main server reference.
    This is useful for testing purposes.

    Args:
        server: Server instance to register globally.
    """
    global MAIN_SERVER
    MAIN_SERVER = server


def get_main_server() -> ClientServer:
    """Return the global main server, creating it if missing.

    Returns:
        ClientServer: Singleton main server instance.
    """
    global MAIN_SERVER
    if MAIN_SERVER is None:
        MAIN_SERVER = ClientServer("MAIN_SERVER")
    return MAIN_SERVER


def get_main_event_bus() -> EventBus:
    """Return the event bus associated with the main server.

    Returns:
        EventBus: Global event bus instance.
    """
    return get_main_server().event_bus
