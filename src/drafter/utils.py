import sys


WEB_RUNTIMES = ("skulpt", "emscripten")


def is_skulpt():
    """
    Detect if we're running inside Skulpt. Relies on the `sys.platform` setting to be "skulpt" or "emscripten".

    Returns:
        bool: True if running inside Skulpt, False otherwise.
    """
    return sys.platform in WEB_RUNTIMES
