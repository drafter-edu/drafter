"""
This module is not actually built in the Skulpt deployment.
Instead, the js/src/bridge/client.ts file is compiled and included
instead.

This module is provided here so that type checkers and IDEs can
understand its existence and provide type information.
"""

from typing import Callable


def load_page(url: str, data: list, target: str, navigate: Callable) -> None:
    pass
