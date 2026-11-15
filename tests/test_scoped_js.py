"""Tests for giving an embedded program a `js` that is its own window.

All the live demos on a documentation page share one Python interpreter,
whose `js` is the page around them. A demo that looked for its own
elements with `js.document.getElementById(...)` searched that outer page.
`make_scoped_builtins` points `import js` at the demo's window, for that
demo's code only.
"""

import ast
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from drafter.helpers import scoped_js
from drafter.helpers.scoped_js import make_scoped_builtins

HOST_PAGE = SimpleNamespace(document=SimpleNamespace(title="The page around"))


@pytest.fixture(autouse=True)
def host_js(monkeypatch):
    """Stand in for Pyodide's `js` module: the window that hosts Python."""
    monkeypatch.setitem(sys.modules, "js", HOST_PAGE)


def make_window(title: str) -> SimpleNamespace:
    return SimpleNamespace(document=SimpleNamespace(title=title))


def run_program(source: str, window: SimpleNamespace) -> dict:
    """Run a program the way an embedded instance is run."""
    program_globals = {
        "__name__": "__main__",
        "__builtins__": make_scoped_builtins(window),
    }
    exec(source, program_globals)
    return program_globals


class TestWhatJsMeans:
    def test_import_js_is_the_programs_window(self):
        window = make_window("Demo A")

        ran = run_program("import js\ntitle = js.document.title", window)

        assert ran["js"] is window
        assert ran["title"] == "Demo A"

    def test_from_js_import(self):
        ran = run_program(
            "from js import document\ntitle = document.title", make_window("Demo A")
        )

        assert ran["title"] == "Demo A"

    def test_import_under_another_name(self):
        ran = run_program(
            "import js as page\ntitle = page.document.title", make_window("Demo A")
        )

        assert ran["title"] == "Demo A"

    def test_import_inside_a_route_called_later(self):
        """A route runs on a click, long after the program's own code."""
        source = (
            "def look():\n"
            "    from js import document\n"
            "    def inner():\n"
            "        import js\n"
            "        return js.document.title\n"
            "    return document.title, inner()\n"
        )
        ran = run_program(source, make_window("Demo A"))

        # Called from outside the program, as Drafter calls a route.
        assert ran["look"]() == ("Demo A", "Demo A")

    def test_two_programs_keep_their_own_windows(self):
        source = "def title():\n    import js\n    return js.document.title\n"
        first = run_program(source, make_window("Demo A"))
        second = run_program(source, make_window("Demo B"))

        assert second["title"]() == "Demo B"
        assert first["title"]() == "Demo A"


class TestWhatIsLeftAlone:
    def test_the_interpreters_own_js_is_untouched(self):
        run_program("import js", make_window("Demo A"))

        import js

        assert sys.modules["js"] is HOST_PAGE
        assert js.document.title == "The page around"

    def test_other_imports_work_as_usual(self):
        ran = run_program(
            "import json\nfrom os import path\nimport os.path as other",
            make_window("Demo A"),
        )

        import json
        import os.path

        assert ran["json"] is json
        assert ran["path"] is os.path
        assert ran["other"] is os.path

    def test_the_real_builtins_are_not_changed(self):
        import builtins

        before = builtins.__import__

        scoped = make_scoped_builtins(make_window("Demo A"))

        assert builtins.__import__ is before
        assert scoped["__import__"] is not before
        assert scoped["print"] is print

    def test_program_can_still_define_classes_and_use_builtins(self):
        ran = run_program(
            "class Pet:\n    pass\ncount = len([Pet(), Pet()])", make_window("Demo A")
        )

        assert ran["count"] == 2


def test_the_helper_imports_nothing_from_drafter():
    """It runs from the bundle as text, beside whatever drafter is installed."""
    tree = ast.parse(Path(scoped_js.__file__).read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    assert not [name for name in imported if name.split(".")[0] == "drafter"]
