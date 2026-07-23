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
    """Loader that executes already-fetched remote module source code.

    Attributes:
        source: The module's Python source text, fetched by `RemoteFinder`.
    """

    def __init__(self, source):
        self.source = source

    def exec_module(self, module):
        """Execute the stored source in the module's namespace.

        Args:
            module: The newly created module object to populate.
        """
        exec(self.source, module.__dict__)


EXTERNAL_IMPORTS = set()
"""Fully qualified names of modules that were loaded from the remote
server, recorded so `expire_remote_imports` can evict them from
`sys.modules` later."""


class RemoteFinder(importlib.abc.MetaPathFinder):
    """Meta-path finder that fetches missing modules over HTTP.

    Appended to `sys.meta_path` when this module is imported, so that any
    import the normal finders cannot satisfy is tried against the server
    hosting the page.
    """

    def find_spec(self, fullname, path=None, target=None):
        """Try to fetch the module as a remote `.py` file.

        Maps the dotted module name to a relative URL (e.g., `pkg.mod`
        becomes `pkg/mod.py`) and fetches it synchronously. On success,
        the name is recorded in `EXTERNAL_IMPORTS` and a spec backed by a
        `RemoteLoader` holding the source is returned.

        Args:
            fullname: Dotted name of the module being imported.
            path: Ignored (standard finder protocol argument).
            target: Ignored (standard finder protocol argument).

        Returns:
            A module spec when the fetch succeeds with HTTP 200, or None
            (letting the import fail normally) on any error or non-200
            response.
        """
        module_path = fullname.split(".")
        path = "/".join(module_path) + ".py"
        url = path

        try:
            response = pyxhr.get(url)
            if response.status_code != 200:
                return None
            text = response.text

            loader = RemoteLoader(text)
            EXTERNAL_IMPORTS.add(fullname)
            return importlib.util.spec_from_loader(fullname, loader)

        except Exception:
            return None


def expire_remote_imports():
    """Remove all remotely imported modules from `sys.modules`.

    Clears `EXTERNAL_IMPORTS` as it goes, so the next import of each
    module re-fetches its source from the server (picking up any changes).
    """
    for fullname in list(EXTERNAL_IMPORTS):
        if fullname in sys.modules:
            del sys.modules[fullname]
        EXTERNAL_IMPORTS.remove(fullname)


sys.meta_path.append(RemoteFinder())
