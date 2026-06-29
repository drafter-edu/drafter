"""
This file should only be imported by Pyodide.
It patches the Python import system to allow importing modules from a remote server.
"""

import sys
import importlib.abc
import importlib.util

from pyodide.http import pyxhr
import js

js.console.log("Patching Python import system to support remote imports...")


# This code allows Python code running in Pyodide to import modules from
# a remote server.
class RemoteLoader(importlib.abc.Loader):
    def __init__(self, source):
        self.source = source

    def exec_module(self, module):
        exec(self.source, module.__dict__)


class RemoteFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        module_path = fullname.split(".")
        path = "/".join(module_path) + ".py"
        url = path

        try:
            response = pyxhr.get(url)
            if response.status_code != 200:
                return None
            text = response.text

            loader = RemoteLoader(text)
            return importlib.util.spec_from_loader(fullname, loader)

        except Exception as e:
            return None


sys.meta_path.append(RemoteFinder())
