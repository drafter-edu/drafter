"""Tests for the main-file id the index page hands to its script.

The page keeps a few things in the browser's localStorage (debug save
slots, the chosen theme, the open debug tab). Every program the development
server runs is served at the same address, so those values used to leak
from one program to the next. The page now carries `DRAFTER_MAIN_FILE_ID`,
a hash of the main file's full path, and the script puts it in its storage
keys (js/src/storage_keys.ts, covered by js/src/__tests__/storage-keys.test.ts).
"""

import os
import re
from pathlib import Path

from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.scaffolding.templating import (
    MAIN_FILE_ID_LENGTH,
    main_file_id,
    render_index_html,
)


def make_system(path: str | None) -> SystemConfiguration:
    app_common = AppCommonConfiguration()
    app_common.prerender_initial_page = False
    return SystemConfiguration(
        bootstrap=BootstrapConfiguration(path=path),
        client_server=ClientServerConfiguration(),
        app_server=AppServerConfiguration(),
        app_builder=AppBuilderConfiguration(),
        app_common=app_common,
    )


def embedded_main_file_id(html: str) -> str:
    (value,) = re.findall(r'window\.DRAFTER_MAIN_FILE_ID = "([^"]*)";', html)
    return value


class TestMainFileId:
    def test_same_file_name_in_two_folders_gets_two_ids(self, tmp_path: Path):
        first = make_system(str(tmp_path / "project_one" / "main.py"))
        second = make_system(str(tmp_path / "project_two" / "main.py"))

        assert main_file_id(first) != main_file_id(second)

    def test_id_is_stable_and_short(self, tmp_path: Path):
        system = make_system(str(tmp_path / "main.py"))

        identifier = main_file_id(system)

        assert identifier == main_file_id(make_system(str(tmp_path / "main.py")))
        assert re.fullmatch(rf"[0-9a-f]{{{MAIN_FILE_ID_LENGTH}}}", identifier)

    def test_relative_path_is_resolved_against_the_working_folder(
        self, tmp_path: Path, monkeypatch
    ):
        # `python main.py` (and Thonny) pass the bare file name, so two
        # projects started that way differ only by their working folder.
        (tmp_path / "one").mkdir()
        (tmp_path / "two").mkdir()
        monkeypatch.chdir(tmp_path / "one")
        in_one = main_file_id(make_system("main.py"))
        monkeypatch.chdir(tmp_path / "two")
        in_two = main_file_id(make_system("main.py"))

        assert in_one != in_two
        assert in_two == main_file_id(make_system(str(tmp_path / "two" / "main.py")))

    def test_id_does_not_reveal_the_path(self, tmp_path: Path):
        folder = tmp_path / "ada_lovelace_homework"
        identifier = main_file_id(make_system(str(folder / "main.py")))

        assert "ada" not in identifier
        assert os.sep not in identifier

    def test_no_main_file_gives_an_empty_id(self):
        assert main_file_id(make_system(None)) == ""


class TestIndexPageCarriesTheId:
    def render(self, system: SystemConfiguration) -> str:
        return render_index_html(
            system=system,
            modified_system={},
            inline_py=True,
            user_code="",
            python_url=None,
            dev_ws_url=None,
            assets_url="/__drafter_assets",
        )

    def test_page_sets_the_id_before_drafters_script_loads(self, tmp_path: Path):
        system = make_system(str(tmp_path / "main.py"))

        html = self.render(system)

        assert embedded_main_file_id(html) == main_file_id(system)
        # The script reads the id while it loads (the saved theme is applied
        # then), so the id has to come first in the page.
        assert html.index("DRAFTER_MAIN_FILE_ID") < html.index("drafter.pyodide.js")

    def test_two_programs_render_pages_with_different_ids(self, tmp_path: Path):
        first = self.render(make_system(str(tmp_path / "one" / "main.py")))
        second = self.render(make_system(str(tmp_path / "two" / "main.py")))

        assert embedded_main_file_id(first) != embedded_main_file_id(second)
