"""
Student-facing commands for registering routes.

Provides the `route` decorator and the `add_route` function, both of which
register a handler function with a server (the main server by default).
"""

from collections.abc import Callable
from typing import TypeVar, cast, overload

from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import get_main_server

T = TypeVar("T", bound=Callable[..., object])
"""Type variable for a decorated route handler, preserving its exact type."""


@overload
def route(url: T) -> T: ...
@overload
def route(
    url: str | None = None, server: ClientServer | None = None
) -> Callable[[T], T]: ...
def route(
    url: str | None | T = None,
    server: ClientServer | None = None,
) -> T | Callable[[T], T]:
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
    url: str, func: Callable[..., object], server: ClientServer | None = None
):
    """Add a route handler to the server.

    Args:
        url: Route path to register.
        func: Function to handle requests to this route.
        server: Server instance to register with (defaults to main server).
    """
    server = server or get_main_server()
    server.add_route(url, func)
