"""Friendly terminal output for Drafter errors raised at the top of a program.

`start_server` already presents a `StudentFacingError` as a titled box with
steps instead of a traceback. Anything raised before `start_server` runs
(`add_website_file("missing.txt")` near the top of a file, say) used to
reach Python's own handler and print a raw traceback, so the explanation
and its "Did you mean" steps were never seen.

`install_student_error_hook` replaces `sys.excepthook` with one that gives
those errors the same box. It is installed when Drafter is imported on the
computer, never in the browser, where errors have an error page.
"""

import os
import sys
import traceback
from collections.abc import Callable
from types import TracebackType
from typing import Any

from drafter.data.errors import StudentFacingError, format_student_facing_error

ExceptHook = Callable[[type[BaseException], BaseException, TracebackType | None], Any]
"""The signature of `sys.excepthook`."""

_PACKAGE_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
"""The folder holding Drafter's own code, used to tell its frames from the
student's."""


def find_student_location(error_traceback: TracebackType | None) -> str:
    """Name the line of the student's program that led to an error.

    Args:
        error_traceback: The traceback of the uncaught error.

    Returns:
        Text like "main.py, line 12" for the innermost frame outside
        Drafter's own code, or an empty string when there is none.
    """
    package_prefix = os.path.normcase(_PACKAGE_DIRECTORY) + os.sep
    for frame in reversed(traceback.extract_tb(error_traceback)):
        filename = os.path.normcase(os.path.abspath(frame.filename))
        if filename.startswith(package_prefix):
            continue
        return f"{os.path.basename(frame.filename)}, line {frame.lineno}"
    return ""


def wants_tracebacks() -> bool:
    """Whether the verbose setting asks for full tracebacks."""
    from drafter.configuration import get_system_configuration

    try:
        return bool(get_system_configuration().bootstrap.verbose)
    except Exception:
        # This runs while Python is already reporting an uncaught error,
        # and building the configuration can fail for its own reasons (a
        # broken config file). A second error here would hide the first.
        return False


def make_student_error_hook(previous_hook: ExceptHook) -> ExceptHook:
    """Build an excepthook that presents Drafter's errors without a traceback.

    Args:
        previous_hook: The hook to hand every other error to, and
            Drafter's own when the verbose setting is on.

    Returns:
        The new hook.
    """

    def show_student_facing_error(
        error_type: type[BaseException],
        error: BaseException,
        error_traceback: TracebackType | None,
    ) -> None:
        if not isinstance(error, StudentFacingError) or wants_tracebacks():
            previous_hook(error_type, error, error_traceback)
            return
        location = find_student_location(error_traceback)
        print(format_student_facing_error(error, location), file=sys.stderr)

    return show_student_facing_error


_installed_hooks: list[ExceptHook] = []
"""The hook `install_student_error_hook` put in place, kept so that a
second call can tell it is already installed."""


def install_student_error_hook() -> None:
    """Make uncaught `StudentFacingError`s print as a friendly box.

    Safe to call more than once. Other errors, and all errors when the
    verbose setting is on, go to whichever hook was installed before.
    """
    if sys.excepthook in _installed_hooks:
        return
    hook = make_student_error_hook(sys.excepthook)
    _installed_hooks.append(hook)
    sys.excepthook = hook
