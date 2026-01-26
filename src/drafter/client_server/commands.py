from typing import Optional
from drafter.monitor.bus import EventBus
from drafter.client_server.client_server import ClientServer

MAIN_SERVER: Optional[ClientServer] = None


def set_main_server(server: ClientServer):
    """
    Sets the main server to the given server. This is useful for testing purposes.

    Args:
        server: The server to set as the main server

    Returns:
        None
    """
    global MAIN_SERVER
    MAIN_SERVER = server


def get_main_server() -> ClientServer:
    """
    Gets the main server. This is useful for testing purposes.

    Args:
        server_name: If the server does not yet exist, then this
                     name will be used to create the server. It will
                     NOT get the server with this name if it already exists, but instead
                     will just return the existing main server.
    Returns:
        The main server.
    """
    global MAIN_SERVER
    if MAIN_SERVER is None:
        MAIN_SERVER = ClientServer("MAIN_SERVER")
    return MAIN_SERVER


def get_main_event_bus() -> EventBus:
    """
    Get the main event bus.

    Returns:
        The main event bus.
    """
    return get_main_server().event_bus
