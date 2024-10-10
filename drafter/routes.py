from typing import Union, Callable
from drafter.server import Server, MAIN_SERVER


def route(url: Union[Callable, str, None] = None, server: Server = MAIN_SERVER):
    """
    Main function to add a new route to the server. Recommended to use as a decorator.
    Once added, the route will be available at the given URL; the function name will be used if no URL is provided.
    When you go to the URL, the function will be called and its return value will be displayed.

    :param url: The URL to add the route to. If None, the function name will be used.
    :param server: The server to add the route to. Defaults to the main server.
    :return: The modified route function.
    """
    if callable(url):
        local_url = url.__name__
        server.add_route(local_url, url)
        return url

    def make_route(func):
        local_url = url
        if url is None:
            local_url = func.__name__
        server.add_route(local_url, func)
        return func

    return make_route
