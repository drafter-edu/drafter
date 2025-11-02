from typing import Union, Callable, Optional
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import get_main_server
from drafter.router.introspect import get_signature


def route(
    url: Union[Callable, str, None] = None, server: Optional[ClientServer] = None
):
    """
    Main function to add a new route to the server. Recommended to use as a decorator.
    Once added, the route will be available at the given URL; the function name will be used if no URL is provided.
    When you go to the URL, the function will be called and its return value will be displayed.

    :param url: The URL to add the route to. If None, the function name will be used.
    :param server: The server to add the route to. Defaults to the main server.
    :return: The modified route function.
    """
    server = server or get_main_server()
    if callable(url):
        local_url = url.__name__
        server.add_route(local_url, url)
        return url

    def make_route(func):
        if url is None:
            local_url = func.__name__
        else:
            local_url = url
        server.add_route(local_url, func)
        return func

    return make_route
