import pathlib
import io
import os
from drafter.configuration import get_system_configuration
from drafter.helpers.utils import is_pyodide, is_web, seek_filename_by_line

# If we can find a start_server line, that's easiest
# If not, then we can look up the stack for the first file that isn't part of Drafter itself,
#    but need to dodge other launching systems like Thonny, pytest, or the Starlette reloader.
# 

def get_user_directory():
    if is_web():
        return "/"

    system = get_system_configuration()
    app_common = system.app_common
    if app_common.user_directory is False:
        found_path = seek_filename_by_line("start_server", app_common.main_filename)
        if found_path:
            return os.path.dirname(found_path)
        
        found_path = seek_filename_by_kind("start_server", "file")
    elif app_common.user_directory is True:
        return os.getcwd()
        
    elif not os.path.isdir(app_common.user_directory):
        if os.path.isfile(app_common.user_directory):
            return os.path.dirname(app_common.user_directory)

    return app_common.user_directory