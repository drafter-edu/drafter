"""Giving an embedded program a `js` that is its own window.

Several Drafter programs can share one Python interpreter, each drawn in
its own iframe (the live demos on a documentation page work this way).
Pyodide's `js` module is the window the interpreter was started in, which
for a demo is the page around it. A demo that wrote
`js.document.getElementById(...)` was searching that outer page and never
found its own elements.

`make_scoped_builtins` builds a replacement for a program's builtins in
which `import js` gives the program's own window. Python looks imports up
through the builtins of the code doing the importing, so the replacement
reaches only the program it is given to: `sys.modules` is not touched, and
Drafter's own `import js` keeps meaning the interpreter's window.

This file is carried inside the browser bundle as text and run with
`exec`, because the bundle and the installed drafter package can be
different versions. It must not import anything from drafter.
"""

import builtins
from collections.abc import Callable
from typing import Any

SCOPED_MODULE_NAME = "js"
"""The module whose import is answered with the program's own window."""


def make_scoped_import(window: Any, fallback: Callable[..., Any]) -> Callable[..., Any]:
    """Build an `__import__` that answers `import js` with a given window.

    Args:
        window: What `import js` should give (an iframe's window).
        fallback: The `__import__` to use for every other module.

    Returns:
        The replacement `__import__`. `import js`, `import js as page`,
        and `from js import document` all go to `window`. Anything else,
        including `import js.something` and relative imports, goes to
        `fallback`.
    """

    def scoped_import(
        name: str,
        globals: Any = None,
        locals: Any = None,
        fromlist: Any = (),
        level: int = 0,
    ) -> Any:
        if level == 0 and name == SCOPED_MODULE_NAME:
            return window
        return fallback(name, globals, locals, fromlist, level)

    return scoped_import


def make_scoped_builtins(window: Any) -> dict[str, Any]:
    """Copy the builtins, with `import js` pointed at a given window.

    Put the result under `"__builtins__"` in the globals a program is run
    with. Every function the program defines then imports through it, also
    when the function is called later (a route run on a click).

    Args:
        window: The window the program is drawn in.

    Returns:
        A new builtins dictionary. The real builtins are left as they are.

    Example:
        ```python
        program_globals = {
            "__name__": "__main__",
            "__builtins__": make_scoped_builtins(frame_window),
        }
        exec("import js\\njs.document.title = 'Mine'", program_globals)
        ```
    """
    scoped = dict(vars(builtins))
    scoped["__import__"] = make_scoped_import(window, builtins.__import__)
    return scoped
