"""
Bridge functions for interacting with the web page in Skulpt.
"""

from drafter.data.request import Request
from drafter.bridge.client import update_site
from typing import Callable
import document  # type: ignore


def make_initial_request() -> Request:
    return Request(0, "load", "index", [], {}, {})


def add_script(src: str) -> None:
    script = document.createElement("script")
    script.src = src
    head = document.getElementsByTagName("head")[0]
    head.appendChild(script)
    return script
