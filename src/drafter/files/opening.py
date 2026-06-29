import pathlib
import io
import os
from typing import Union
from drafter.configuration import get_system_configuration
from drafter.helpers.utils import is_pyodide, is_web
import builtins

_BUILTIN_OPEN = builtins.open


def open(file_path, mode="r", *args, **kwargs):
    """
    Opens files for reading or writing, with special handling for web environments.
    This is a Drafter-specific implementation that abstracts away differences between running in a web context and a standard Python environment.

    Args:
        file_path (_type_): The path to the file to open. In a web environment, this could be a virtual path or identifier rather than an actual filesystem path.
        mode (str, optional): The mode in which to open the file (e.g., "r" for read, "w" for write). Defaults to "r".
        encoding (str, optional): The encoding to use when opening the file. Defaults to "utf-8".
    Returns:
        A file-like object that can be used to read from or write to the specified file path, with behavior adapted to the execution environment.
    """
    if not isinstance(file_path, (str, pathlib.Path)):
        raise ValueError(
            f"Invalid file path: {file_path}. Must be a string or pathlib.Path."
        )

    # TODO: Check config setting for whether absolute paths are allowed
    # TODO: Check config setting to decide whether we should use the students' main file path, the current working directory, or an explicit path

    if is_pyodide():
        # In Pyodide, we might need to fetch the file if it is not available normally.
        actual_path = file_path

        try:
            found_file = _BUILTIN_OPEN(actual_path, mode, *args, **kwargs)
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                from js import XMLHttpRequest

                req = XMLHttpRequest.new()
                req.open("GET", str(actual_path), False)
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


def get_drafter_path(path: Union[str, pathlib.Path]) -> pathlib.Path:
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
