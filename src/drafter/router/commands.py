from typing import Union, Callable, Optional, TypeVar, overload, cast
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import get_main_server

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
    """Register a route handler with the server.

    Can be used as a decorator with or without arguments. If url is not
    provided, the function name is used as the route path.

    Args:
        url: Route path, or the function itself if used without parentheses.
        server: Server instance to register with (defaults to main server).

    Returns:
        Modified route function, or decorator if url was provided.

    Example:
        @route
        def index(state):
            return Page(state, [])

        @route("/custom")
        def custom(state):
            return Page(state, [])
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


def add_route(
    url: str, func: Callable[..., object], server: Optional[ClientServer] = None
):
    """Add a route handler to the server.

    Args:
        url: Route path to register.
        func: Function to handle requests to this route.
        server: Server instance to register with (defaults to main server).
    """
    server = server or get_main_server()
    server.add_route(url, func)
