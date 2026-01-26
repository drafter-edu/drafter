from typing import Union, Callable, Optional, TypeVar, overload, ParamSpec, cast
from functools import wraps
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import get_main_server
from drafter.router.introspect import get_signature

T = TypeVar("T", bound=Callable[..., object])

@overload
def route(url: T) -> T: ...
@overload
def route(
    url: Union[str, None] = None, server: Optional[ClientServer] = None
) -> Callable[[T], T]: ...
def route(
    url: Union[str, None, T] = None,
    server: Optional[ClientServer] = None,
) -> Union[T, Callable[[T], T]]:
    """
    Main function to add a new route to the server. Recommended to use as a decorator.
    Once added, the route will be available at the given URL; the function name will be used if no URL is provided.
    When you go to the URL, the function will be called and its return value will be displayed.

    Args:
        url: The URL to add the route to. If None, the function name will be used.
        server: The server to add the route to. Defaults to the main server.

    Returns:
        The modified route function.
    """

    server = server or get_main_server()
    if callable(url):
        func = cast(T, url)
        local_url = func.__name__
        server.add_route(local_url, func)
        return func
    
    def make_route(func: T) -> T:
        local_url = url if url is not None else func.__name__
        server.add_route(local_url, func)
        return func

    return make_route
