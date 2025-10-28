import html
import os
import traceback
from dataclasses import dataclass, asdict, replace, field, fields
from functools import wraps
from typing import Any, Optional, List, Tuple, Union
import json
import inspect
import pathlib

from drafter.response import Response
from drafter.routes import Router


@dataclass
class Server:
    """
    Represents a server that can handle routes.
    """

    custom_name: str
    state: Any

    def __init__(self, custom_name: str) -> None:
        self.router = Router()
        self.state = None

    def visit(self, url: str, *args, **kwargs) -> Any:
        """
        Visits the given URL on the server, calling the associated function.

        :param url: The URL to visit.
        :param args: Positional arguments to pass to the route function.
        :param kwargs: Keyword arguments to pass to the route function.
        :return: The result of the route function.
        """
        print("Visiting URL:", url)
        route_func = self.router.get_route(url)
        if route_func is None:
            raise ValueError(f"No route found for URL: {url}")
        print("Calling", route_func, args)
        page = route_func(self.state, *args, **kwargs)
        return Response(page)


MAIN_SERVER = Server(custom_name="MAIN_SERVER")


def set_main_server(server: Server):
    """
    Sets the main server to the given server. This is useful for testing purposes.

    :param server: The server to set as the main server
    :return: None
    """
    global MAIN_SERVER
    MAIN_SERVER = server


def get_main_server() -> Server:
    """
    Gets the main server. This is useful for testing purposes.

    :return: The main server
    """
    return MAIN_SERVER
