from drafter.monitor.bus import EventBus
from drafter.client_server.client_server import ClientServer

MAIN_SERVER = ClientServer(custom_name="MAIN_SERVER")


def set_main_server(server: ClientServer):
    """
    Sets the main server to the given server. This is useful for testing purposes.

    :param server: The server to set as the main server
    :return: None
    """
    global MAIN_SERVER
    MAIN_SERVER = server


def get_main_server() -> ClientServer:
    """
    Gets the main server. This is useful for testing purposes.

    :return: The main server
    """
    return MAIN_SERVER


def get_main_event_bus() -> EventBus:
    """
    Get the main event bus.

    :return: The main event bus.
    """
    return get_main_server().event_bus
