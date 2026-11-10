"""Finding the libraries a program imports, and which of them are missing.

In the browser, Pyodide installs the libraries bundled with it when it
sees them imported. A library outside that bundle (seaborn, for example)
is left alone, and the program then stops with `ModuleNotFoundError`.
`find_missing_imports` lists the imports nothing can satisfy yet, so the
runtime can try to install each one from PyPI before the program runs.

"Nothing can satisfy" is decided by Python's own import machinery, which
in the browser includes the finder that fetches a student's other files
from the site (see `drafter.files.patch_pyodide`). A student's own
`helpers.py` is therefore always found first and is never looked up on
PyPI, even though a package named `helpers` exists there.
"""

import ast
import importlib.metadata
import importlib.util
import re
import sys


def find_imported_modules(code: str) -> list[str]:
    """List the top-level modules a program imports, in order of appearance.

    Both `import a.b` and `from a.b import c` count as importing `a`.
    Relative imports (`from . import x`) are skipped, since they can only
    refer to the program's own files. Imports anywhere in the file are
    included, even inside functions or `try` blocks.

    Args:
        code: Python source code.

    Returns:
        The distinct top-level module names. Empty when the code has a
        syntax error, which is reported elsewhere.

    Example:
        ```python
        find_imported_modules("import seaborn as sns\\nfrom os import path")
        # ['seaborn', 'os']
        ```
    """
    try:
        # Top-level await is allowed in the browser, so allow it here too.
        tree = compile(
            code,
            "<program>",
            "exec",
            flags=ast.PyCF_ONLY_AST | ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
        )
    except SyntaxError:
        return []
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            candidates = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            candidates = [node.module]
        else:
            continue
        for candidate in candidates:
            top_level = candidate.split(".")[0]
            if top_level and top_level not in names:
                names.append(top_level)
    return names


def is_importable(module_name: str) -> bool:
    """Whether Python could import a top-level module right now.

    Asks the import machinery without importing anything. A finder that
    fails while answering is treated as "yes": guessing "no" would send a
    name that may be the student's own file off to PyPI.

    Args:
        module_name: A top-level module name, such as `seaborn`.

    Returns:
        True if the module is already loaded, built in, or can be found.
    """
    if module_name in sys.modules or module_name in sys.stdlib_module_names:
        return True
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return True


def find_missing_imports(code: str) -> list[str]:
    """List the imported modules that nothing can currently provide.

    Args:
        code: Python source code.

    Returns:
        The top-level module names from `find_imported_modules` that are
        not importable, in order of appearance.

    Example:
        ```python
        find_missing_imports("import json\\nimport seaborn")
        # ['seaborn'] when seaborn is not installed, otherwise []
        ```
    """
    return [name for name in find_imported_modules(code) if not is_importable(name)]


REQUIREMENT_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
"""The project name at the front of a requirement such as `sym>=0.3.7`."""


def find_missing_requirements(distributions: list[str]) -> list[str]:
    """List the declared dependencies of installed packages that are absent.

    Used after wheels are installed from a wheel index without dependency
    resolution: the index supplies the pure-Python packages, and this
    reports what else they declare they need, so the runtime can fetch
    those (for example `sympy` from the browser's own distribution).

    Requirements that apply only to an extra (`; extra == "docs"`) are
    skipped. Other environment markers are not evaluated, so a requirement
    meant for another platform may be reported; trying to install it is
    harmless.

    Args:
        distributions: Installed distribution names to inspect. Names that
            are not installed are ignored.

    Returns:
        The distinct missing requirement names, sorted.

    Example:
        ```python
        find_missing_requirements(["chempy"])
        # ['numpy', 'sympy'] when those are not installed yet
        ```
    """
    missing: set[str] = set()
    for distribution in distributions:
        try:
            requirements = importlib.metadata.requires(distribution) or []
        except importlib.metadata.PackageNotFoundError:
            continue
        for text in requirements:
            specifier, _, marker = text.partition(";")
            if "extra" in marker:
                continue
            match = REQUIREMENT_NAME_PATTERN.match(specifier.strip())
            if not match:
                continue
            name = match.group(0)
            try:
                importlib.metadata.distribution(name)
            except importlib.metadata.PackageNotFoundError:
                missing.add(name)
    return sorted(missing)
