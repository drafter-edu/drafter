from typing import Callable
from functools import wraps
import sys


WEB_RUNTIMES = ("skulpt", "emscripten")


def is_skulpt():
    """
    Detect if we're running inside Skulpt. Relies on the `sys.platform` setting to be "skulpt" or "emscripten".

    Returns:
        bool: True if running inside Skulpt, False otherwise.
    """
    return sys.platform in WEB_RUNTIMES


def only_skulpt(callable: Callable) -> Callable:
    """
    Decorator to make a function only run in Skulpt (web) environments.
    If not in Skulpt, the function will return None.

    :param callable: The function to decorate.
    :return: The decorated function.
    """

    @wraps(callable)
    def wrapper(*args, **kwargs):
        if is_skulpt():
            return callable(*args, **kwargs)
        return None

    return wrapper


def not_in_skulpt(callable: Callable) -> Callable:
    """
    Decorator to make a function only run outside of Skulpt (web) environments.
    If in Skulpt, the function will return None.

    :param callable: The function to decorate.
    :return: The decorated function.
    """

    @wraps(callable)
    def wrapper(*args, **kwargs):
        if not is_skulpt():
            return callable(*args, **kwargs)
        return None

    return wrapper


def seek_file_by_line(line, missing_value=None):
    """
    Seeks and returns the filename of a source file by examining the stack trace for a line
    matching the given string. This function allows looking into the recent call stack to
    find where a specific line of code was executed. If no match is found, an optional
    missing value can be returned.

    :param line: The string to search for in the stack trace. It is compared with the
        stripped contents of each entry in the stack trace.
    :type line: str
    :param missing_value: An optional value to return if no match is found in the stack
        trace. Defaults to None.
    :type missing_value: Any
    :return: The filename associated with the supplied line in the stack trace if found,
        or the missing_value if no match is located.
    :rtype: str | None
    """
    try:
        from traceback import extract_stack

        trace = extract_stack()
        for data in trace:
            if data[3].strip().startswith(line):  # type: ignore
                return data[0]
        return missing_value
    except Exception as e:
        print(f"Error seeking file by line: {e}")
        return missing_value
