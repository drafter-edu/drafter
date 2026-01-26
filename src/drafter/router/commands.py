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
