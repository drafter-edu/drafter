from typing import Union, Callable, Optional
from dataclasses import dataclass


@dataclass
class Router:
    """
    Handles routing of URLs to functions within a server.
    """

    def __init__(self) -> None:
        self.routes = {}

    def get_route(self, url: str) -> Optional[Callable]:
        """
        Retrieves the function associated with a given URL.

        :param url: The URL to look up.
        :return: The function associated with the URL, or None if not found.
        """
        return self.routes.get(url)

    def add_route(self, url: str, func: Callable) -> None:
        """
        Adds a new route to the server.

        :param url: The URL to add the route to.
        :param func: The function to call when the route is accessed.
        """
        self.routes[url] = func
