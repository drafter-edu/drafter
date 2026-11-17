"""
This file should only be imported by Pyodide.
It patches the Python import system to allow importing modules from a remote
server, and makes Matplotlib draw off screen so that `plt.show()` adds
nothing to the page.
"""

import importlib.abc
import importlib.util
import os
import sys
import warnings

from pyodide.http import pyxhr  # type: ignore

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
        """Try to fetch the module as a remote `.py` file or package.

        Maps the dotted module name to a relative URL (e.g., `pkg.mod`
        becomes `pkg/mod.py`) and fetches it synchronously. If there is no
        such file, tries the name as a package folder instead
        (`pkg/mod/__init__.py`), so a student's `import my_project` works
        in the browser for a `my_project/` folder just as it does in
        regular Python. On success, the name is recorded in
        `EXTERNAL_IMPORTS` and a spec backed by a `RemoteLoader` holding
        the source is returned; package specs are marked as packages so
        their submodules and relative imports resolve.

        Args:
            fullname: Dotted name of the module being imported.
            path: Ignored (standard finder protocol argument).
            target: Ignored (standard finder protocol argument).

        Returns:
            A module spec when a fetch succeeds with HTTP 200, or None
            (letting the import fail normally) when neither the module file
            nor the package's `__init__.py` could be fetched.
        """
        base_url = "/".join(fullname.split("."))
        candidates = ((base_url + ".py", False), (base_url + "/__init__.py", True))
        for url, is_package in candidates:
            try:
                response = pyxhr.get(url)
            except Exception:
                continue
            if response.status_code != 200:
                continue
            loader = RemoteLoader(response.text)
            EXTERNAL_IMPORTS.add(fullname)
            return importlib.util.spec_from_loader(
                fullname, loader, origin=url, is_package=is_package
            )
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


MATPLOTLIB_SHOW_WARNING = "FigureCanvasAgg is non-interactive"
"""The start of the warning Matplotlib gives when `plt.show()` is called and
figures are drawn off screen. `draw_matplotlib_off_screen` silences it."""


def draw_matplotlib_off_screen() -> None:
    """Make `plt.show()` do nothing in the browser.

    In the browser, Matplotlib normally answers `plt.show()` by adding a
    figure window of its own to the bottom of the web page, outside the
    Drafter site, and one more for every later call. A Drafter page
    shows a chart with `MatPlotLibPlot`, so nothing should appear for
    `plt.show()`, whether the program calls it or a library does on the
    program's behalf.

    Drawing off screen (Matplotlib's "Agg" backend) gives that: `plt.show()`
    leaves the page alone and the figure stays open for `MatPlotLibPlot`.
    The backend is chosen through the `MPLBACKEND` environment variable,
    which Matplotlib reads when it is first imported, so this must run
    before the program does. A value that is already set is kept.

    Matplotlib warns on every `plt.show()` that an off-screen figure cannot
    be shown. That warning is silenced: it would fill the console with a
    message about something the program is not expected to change.
    """
    os.environ.setdefault("MPLBACKEND", "Agg")
    warnings.filterwarnings(
        "ignore", message=MATPLOTLIB_SHOW_WARNING, category=UserWarning
    )


sys.meta_path.append(RemoteFinder())
draw_matplotlib_off_screen()
