import pathlib
import io
import os
from drafter.configuration import get_system_configuration
from drafter.helpers.utils import is_pyodide, is_web


_BUILTIN_OPEN = open


def open(file_path, mode="r", encoding="utf-8", **kwargs):
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
        raise ValueError(f"Invalid file path: {file_path}. Must be a string or pathlib.Path.")
    
    # TODO: Check config setting for whether absolute paths are allowed
    # TODO: Check config setting to decide whether we should use the students' main file path, the current working directory, or an explicit path
    system = get_system_configuration()
    user_directory = system.app_common.user_directory
    
    if is_pyodide():
        # In Pyodide, we might need to fetch the file if it is not available normally.
        actual_path = file_path
        from pyodide.http import pyxhr
        try:
            found_file = _BUILTIN_OPEN(actual_path, mode, encoding=encoding, **kwargs)
        except Exception as e:
            # If the file is not found, we can try to fetch it via HTTP if it's a relative path
            response = pyxhr.get(actual_path)
            if response.status_code == 200:
                return io.StringIO(response.text)
            else:
                raise FileNotFoundError(f"File not found: {actual_path}")
        return found_file
    if is_web():
        actual_path = file_path
        return _BUILTIN_OPEN(actual_path, mode, encoding=encoding, **kwargs)
    else:
        # Need to handle the case where an absolute URL was given
        if isinstance(file_path, str) and (file_path.startswith("http://") or file_path.startswith("https://")):
            from urllib.request import urlopen
            response = urlopen(file_path)
            if response.status != 200:
                raise FileNotFoundError(f"URL not found: {file_path}")
            return io.StringIO(response.read().decode(encoding))
        else:
            actual_path = pathlib.Path(file_path)
            if not actual_path.is_absolute():
                if user_directory is not False:
                    actual_path = pathlib.Path(user_directory) / actual_path
                else:
                    actual_path = pathlib.Path.cwd() / actual_path
            return _BUILTIN_OPEN(actual_path, mode, encoding=encoding, **kwargs)