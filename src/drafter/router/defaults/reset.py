from drafter.client_server.commands import get_main_server
from drafter.payloads.kinds.redirect import Redirect


def default_reset(state):
    """Default reset route handler.

    Args:
        state: Current application state.

    Returns:
        Redirect: Redirect to the index page.
    """
    # TODO: Use the DI parameter _server instead of get_main_server
    get_main_server().state.reset()
    return Redirect("index")
