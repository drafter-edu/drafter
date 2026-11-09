"""Tests for finding a program's imports and which of them are missing.

The browser runtime uses `find_missing_imports` to decide which libraries
to try installing from PyPI before a student's program runs.
"""

import importlib.abc
import importlib.util
import sys

import pytest

from drafter.helpers.imports import (
    find_imported_modules,
    find_missing_imports,
    is_importable,
)

MISSING = "drafter_test_library_that_does_not_exist"


class TestFindImportedModules:
    def test_plain_and_from_imports(self):
        code = "import seaborn as sns\nfrom os import path\nimport json"

        assert find_imported_modules(code) == ["seaborn", "os", "json"]

    def test_submodules_count_as_their_top_level_package(self):
        code = "import matplotlib.pyplot as plt\nfrom scipy.stats import norm"

        assert find_imported_modules(code) == ["matplotlib", "scipy"]

    def test_several_names_on_one_line(self):
        assert find_imported_modules("import os, sys, seaborn") == [
            "os",
            "sys",
            "seaborn",
        ]

    def test_each_module_is_listed_once(self):
        code = "import numpy\nimport numpy as np\nfrom numpy import array"

        assert find_imported_modules(code) == ["numpy"]

    def test_relative_imports_are_skipped(self):
        code = "from . import helpers\nfrom .pets import Dog\nfrom .. import base"

        assert find_imported_modules(code) == []

    def test_imports_inside_functions_and_try_blocks_are_found(self):
        code = (
            "def chart():\n"
            "    import seaborn\n"
            "try:\n"
            "    import pandas\n"
            "except ImportError:\n"
            "    pandas = None\n"
        )

        assert sorted(find_imported_modules(code)) == ["pandas", "seaborn"]

    def test_text_that_only_mentions_an_import_is_ignored(self):
        code = 'note = "import seaborn"\n# import pandas\n'

        assert find_imported_modules(code) == []

    def test_a_syntax_error_gives_no_imports(self):
        assert find_imported_modules("import seaborn\ndef broken(:\n") == []


class TestIsImportable:
    def test_standard_library(self):
        assert is_importable("json")
        assert is_importable("dataclasses")

    def test_installed_package(self):
        assert is_importable("drafter")
        assert is_importable("pytest")

    def test_unknown_name(self):
        assert not is_importable(MISSING)

    def test_a_finder_that_crashes_counts_as_importable(self, monkeypatch):
        def crash(name, package=None):
            raise RuntimeError("finder exploded")

        monkeypatch.setattr(importlib.util, "find_spec", crash)

        assert is_importable(MISSING)


class TestFindMissingImports:
    def test_reports_only_what_cannot_be_imported(self):
        code = f"import json\nimport {MISSING}\nfrom drafter import *"

        assert find_missing_imports(code) == [MISSING]

    def test_nothing_missing(self):
        assert find_missing_imports("import json\nfrom drafter import *") == []

    def test_a_students_own_file_is_never_reported(self):
        """In the browser, a finder on `sys.meta_path` fetches the student's
        other files. Anything such a finder can provide must not be sent to
        PyPI, even though an unrelated package of that name may exist there."""

        class StudentFileFinder(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "helpers_for_my_site":
                    return importlib.util.spec_from_loader(fullname, loader=None)
                return None

        finder = StudentFileFinder()
        sys.meta_path.append(finder)
        try:
            code = f"import helpers_for_my_site\nimport {MISSING}"

            assert find_missing_imports(code) == [MISSING]
        finally:
            sys.meta_path.remove(finder)

    @pytest.mark.parametrize("code", ["", "x = 1\n", "def broken(:\n"])
    def test_programs_without_usable_imports(self, code):
        assert find_missing_imports(code) == []
