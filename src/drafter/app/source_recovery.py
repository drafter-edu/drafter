"""Recover the student's main source when no saved file is available.

Editors like Thonny can run an editor buffer that has never been saved. In
that case the interpreter is launched the same way as `python -c <code>`:
there is no `__file__`, and `sys.argv` is just `['-c']`. Drafter normally
reads the student's main file from disk to ship it to the browser, so with
no file it would otherwise fail with a confusing 500 on the first request.

This module provides two things:

* detection of "placeholder" script arguments that are not real paths, and
* a best-effort hook that pulls the unsaved source directly out of Thonny's
  backend, so that running an unsaved file in Thonny "just works".
"""

import importlib
import os

#: Values that `sys.argv[0]` takes when Python was started without a script
#: file (`python -c ...`, `python -m ...`, `python -` / stdin). None of these
#: is a usable path to the student's code.
PLACEHOLDER_SCRIPT_ARGUMENTS = frozenset({"-c", "-m", "-", ""})

#: Synthetic filename used when the source was recovered from memory rather
#: than read from disk. It is what the browser and error log call the file.
UNSAVED_SOURCE_FILENAME = "unsaved_thonny_script.py"


def is_placeholder_script_argument(argument: str | None) -> bool:
    """Check whether a command line argument is a stand-in rather than a path.

    Args:
        argument: The candidate main-file argument (typically `sys.argv[0]`).

    Returns:
        True if the argument cannot possibly name the student's file.
    """
    return argument is None or argument.strip() in PLACEHOLDER_SCRIPT_ARGUMENTS


def get_thonny_main_source() -> str | None:
    """Fetch the source of the script Thonny is currently running, if any.

    Thonny's CPython backend keeps the command it is executing (including
    the full editor text) on its current executor. This reaches into those
    private attributes; it is deliberately defensive so that any change to
    Thonny's internals simply makes it return None.

    Returns:
        The source text of the running Thonny script, or None if we are not
        running under Thonny (or its internals look different than expected).
    """
    try:
        cp_back = importlib.import_module("thonny.plugins.cpython_backend.cp_back")
        backend = cp_back.get_backend()
        executor = backend._current_executor
        if executor is None:
            return None

        cmd = executor._original_cmd
        source = getattr(cmd, "source", None)
    except (ImportError, AttributeError):
        return None
    return source if isinstance(source, str) else None


def main_file_is_available(path: str | None) -> bool:
    """Check whether the configured main file can actually be read.

    Args:
        path: The configured `bootstrap.path`, possibly None.

    Returns:
        True if `path` names an existing file on disk.
    """
    if path is None or is_placeholder_script_argument(path):
        return False
    return os.path.isfile(path)


def recover_main_source(path: str | None) -> str | None:
    """Try to obtain the student's main source when the file is unavailable.

    Only consults in-memory fallbacks (currently just Thonny) when the file
    on disk genuinely cannot be used; a readable file always wins.

    Args:
        path: The configured `bootstrap.path`, possibly None.

    Returns:
        The recovered source text, or None if the file is available (read it
        instead) or no fallback could supply the source.
    """
    if main_file_is_available(path):
        return None
    return get_thonny_main_source()
