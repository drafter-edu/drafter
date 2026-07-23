"""Drafter's replacement for the built-in `open`.

Importing this module installs the `open` function defined here over
`builtins.open`. The replacement adapts file access to the execution
environment: in Pyodide, relative paths resolve inside the current
instance's virtual folder and missing files are fetched over HTTP
relative to the page URL; outside the web, `http://`/`https://` paths
are downloaded into in-memory file objects and relative paths resolve
against the configured user directory (see `get_drafter_path`).
"""

import pathlib
import io
import os
from typing import Union
from drafter.configuration import get_system_configuration
from drafter.helpers.utils import is_pyodide, is_web
import builtins

_BUILTIN_OPEN = builtins.open


def _resolve_instance_path(
    file_path: Union[str, pathlib.Path, os.PathLike],
) -> Union[str, pathlib.Path, os.PathLike]:
    """Resolve a relative path inside the current instance's virtual folder.

    When several Drafter instances share one interpreter (each in its own
    iframe), every instance owns a subtree of the shared virtual filesystem
    (e.g. "/instances/demo-1"). Absolute paths and the single-instance case
    (no instance root configured) pass through unchanged.
    """
    from drafter.client_server.commands import get_current_instance_root

    instance_root = get_current_instance_root()
    if instance_root is None:
        return file_path
    path = pathlib.PurePosixPath(str(file_path))
    if path.is_absolute():
        return file_path
    return str(pathlib.PurePosixPath(instance_root) / path)


def open(file_path, mode="r", *args, **kwargs):
    """
    Opens files for reading or writing, with special handling for web environments.

    This is Drafter's replacement for the built-in `open` (it is installed
    over `builtins.open` when this module is imported), abstracting away
    differences between running in a web context and a standard Python
    environment. In Pyodide, relative paths resolve inside the current
    instance's virtual folder, and files missing from the virtual
    filesystem are fetched over HTTP relative to the page URL. Outside the
    web, `http://`/`https://` paths are downloaded and returned as
    in-memory file objects, and relative paths resolve against the
    configured user directory (or the current working directory).

    Args:
        file_path: The path to the file to open. In a web environment, this
            may be a virtual path resolved inside the instance's folder; it
            may also be an `http://` or `https://` URL.
        mode: The mode in which to open the file (e.g., "r" for read,
            "w" for write). Defaults to "r".
        *args: Additional positional arguments passed through to the
            underlying built-in `open`.
        **kwargs: Additional keyword arguments passed through to the
            underlying built-in `open` (e.g., `encoding`).

    Returns:
        A file-like object for reading from or writing to the given path,
        with behavior adapted to the execution environment.

    Raises:
        ValueError: If `file_path` is not a string, `pathlib.Path`, or
            `os.PathLike`.
        FileNotFoundError: If the file cannot be found locally or fetched
            over HTTP.
    """
    if not isinstance(file_path, (str, pathlib.Path, os.PathLike)):
        raise ValueError(
            f"Invalid file path: {file_path}. Must be a string, pathlib.Path, or os.PathLike."
        )

    # TODO: Check config setting for whether absolute paths are allowed
    # TODO: Check config setting to decide whether we should use the students' main file path, the current working directory, or an explicit path

    if is_pyodide():
        # In Pyodide, we might need to fetch the file if it is not available normally.
        # Relative paths resolve inside the current instance's folder so that
        # several instances sharing one interpreter keep separate files.
        actual_path = _resolve_instance_path(file_path)

        try:
            found_file = _BUILTIN_OPEN(actual_path, mode, *args, **kwargs)
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                from js import XMLHttpRequest

                req = XMLHttpRequest.new()
                # Fetch with the ORIGINAL path: the network fallback resolves
                # relative to the page URL, not the instance's virtual folder.
                req.open("GET", str(file_path), False)
                req.overrideMimeType("text/plain; charset=x-user-defined")
                req.send()
                if req.status == 200:
                    if "b" in mode:
                        r = bytes(ord(c) & 0xFF for c in req.responseText)
                        return io.BytesIO(r)
                    return io.StringIO(req.responseText)
                else:
                    raise FileNotFoundError(f"File not found: {actual_path}")
                # from pyodide.http import pyxhr

                # # If the file is not found, we can try to fetch it via HTTP if it's a relative path
                # response = pyxhr.get(str(actual_path))
                # print(response._xhr.response.encode("utf-8"))
                # print(response._xhr.responseText.encode("utf-8"))
                # if response.status_code == 200:
                #     if "b" in mode:
                #         return io.BytesIO(response._xhr.response)
                #     return io.StringIO(response.text)
                # else:
                #     raise FileNotFoundError(f"File not found: {actual_path}")
            else:
                raise e
        return found_file

    if is_web():
        # TODO: Handle skulpt file handling
        actual_path = file_path
        return _BUILTIN_OPEN(actual_path, mode, *args, **kwargs)
    else:
        # Need to handle the case where an absolute URL was given
        if isinstance(file_path, str) and (
            file_path.startswith("http://") or file_path.startswith("https://")
        ):
            from urllib.request import urlopen

            response = urlopen(file_path)
            if response.status != 200:
                raise FileNotFoundError(f"URL not found: {file_path}")
            if "b" in mode:
                return io.BytesIO(response.read())
            if "encoding" in kwargs:
                return io.StringIO(response.read().decode(kwargs["encoding"]))
            return io.StringIO(response.read().decode())
        else:
            actual_path = get_drafter_path(file_path)
            return _BUILTIN_OPEN(actual_path, mode, *args, **kwargs)


def get_drafter_path(
    path: Union[str, pathlib.Path, os.PathLike],
) -> pathlib.Path:
    """Resolve a path against Drafter's configured user directory.

    Absolute paths are returned unchanged (as a `pathlib.Path`). Relative
    paths are joined onto the user directory from the system
    configuration's bootstrap settings; when no user directory is
    configured (the setting is False), the current working directory is
    used instead.

    Args:
        path: The path to resolve; a string, `pathlib.Path`, or
            `os.PathLike`.

    Returns:
        pathlib.Path: The resolved path.
    """
    system = get_system_configuration()
    user_directory = system.bootstrap.get_user_directory()
    actual_path = pathlib.Path(path)
    if not actual_path.is_absolute():
        if user_directory is not False:
            actual_path = pathlib.Path(user_directory) / actual_path
        else:
            actual_path = pathlib.Path.cwd() / actual_path
    return actual_path


builtins.open = open
