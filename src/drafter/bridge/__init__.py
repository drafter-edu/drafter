"""
Bridge functions for interacting with the web page in Skulpt.
"""

from drafter.data.request import Request
from drafter.data.response import Response
from drafter.bridge.client import update_site
from typing import Callable

try:
    import document  # type: ignore
except ImportError:
    document = None  # type: ignore


def make_initial_request() -> Request:
    return Request(0, "load", "index", [], {}, {})


def dispatch_response(response: Response, callback: Callable):
    """
    Dispatches a response to the appropriate handler based on the payload type.
    
    This function checks the type of the response payload and calls the
    appropriate handler function. Different payload types (Page, Fragment,
    Redirect, Download, Progress, Update) are handled differently.
    
    :param response: The response from the server to dispatch.
    :param callback: The callback function to handle navigation.
    :return: The outcome of processing the response.
    """
    # For now, delegate to update_site for all response types
    # Individual handlers will be implemented in the TypeScript client
    return update_site(response, callback)


def add_script(src: str) -> None:
    if document is None:
        return None
    script = document.createElement("script")
    script.src = src
    head = document.getElementsByTagName("head")[0]
    head.appendChild(script)
    return script
