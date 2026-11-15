"""Default "--reset" route, resetting site state and redirecting to index."""

from drafter.client_server.client_server import ClientServer
from drafter.payloads.kinds.redirect import Redirect


def default_reset(state, _server: ClientServer):
    """Default reset route handler.

    Resets the state of the server that is handling this request, which
    is not always the main server: a page can hold several Drafter sites.

    Args:
        state: Current application state.
        _server: The server handling the request (injected by Drafter).

    Returns:
        Redirect: Redirect to the index page.
    """
    _server.state.reset()
    return Redirect("index")
