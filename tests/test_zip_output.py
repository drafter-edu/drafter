"""Tests for the builder's `zip_output` setting.

`--zip-output` used to be accepted, stored, and never read.
"""

import zipfile
from pathlib import Path

import pytest

from drafter.builder.build import compile_site, zip_output_directory
from drafter.client_server.client_server import ClientServer
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.configuration import (
    _reset_system_for_testing,
    _set_system_for_testing,
)


def make_system(tmp_path: Path, zip_output: bool) -> SystemConfiguration:
    """A compile-mode system whose output and assets both live under tmp_path."""
    main_file = tmp_path / "main.py"
    main_file.write_text("from drafter import *\nstart_server()\n", encoding="utf-8")
    assets = tmp_path / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "placeholder.txt").write_text("asset", encoding="utf-8")
    return SystemConfiguration(
        bootstrap=BootstrapConfiguration(path=str(main_file), mode="compile_site"),
        client_server=ClientServerConfiguration(),
        app_server=AppServerConfiguration(),
        app_builder=AppBuilderConfiguration(
            output_directory=str(tmp_path / "dist"),
            pyodide_package_style="cdn",
            warn_missing_info=False,
            zip_output=zip_output,
        ),
        app_common=AppCommonConfiguration(
            prerender_initial_page=False, asset_directory=str(assets)
        ),
    )


@pytest.fixture
def build(tmp_path):
    """Compile a small site into `tmp_path / "dist"`, with or without a zip."""

    def run(zip_output: bool) -> None:
        system = make_system(tmp_path, zip_output)
        _set_system_for_testing(system)
        compile_site(system, ClientServer(custom_name="ZIP_OUTPUT_TEST"), None)

    yield run
    _reset_system_for_testing()


class TestCompileSite:
    def test_no_zip_by_default(self, build, tmp_path):
        build(zip_output=False)

        assert (tmp_path / "dist" / "index.html").exists()
        assert not (tmp_path / "dist.zip").exists()

    def test_zip_is_written_next_to_the_output_folder(self, build, tmp_path, capsys):
        build(zip_output=True)

        zip_path = tmp_path / "dist.zip"
        assert zip_path.exists()
        assert str(zip_path.resolve()) in capsys.readouterr().out
        with zipfile.ZipFile(zip_path) as archive:
            names = set(archive.namelist())
        # Paths are relative to the site, so it unpacks ready to serve.
        assert "index.html" in names
        assert "404.html" in names
        assert any(name.endswith("placeholder.txt") for name in names)

    def test_building_twice_does_not_zip_the_zip(self, build, tmp_path):
        build(zip_output=True)
        build(zip_output=True)

        with zipfile.ZipFile(tmp_path / "dist.zip") as archive:
            names = archive.namelist()
        assert not any(name.endswith(".zip") for name in names)
        assert not list((tmp_path / "dist").rglob("*.zip"))


class TestZipOutputDirectory:
    def test_keeps_folders_and_file_contents(self, tmp_path):
        site = tmp_path / "public"
        (site / "images").mkdir(parents=True)
        (site / "index.html").write_text("<p>Ada</p>", encoding="utf-8")
        (site / "images" / "corgi.txt").write_text("woof", encoding="utf-8")

        zip_path = zip_output_directory(site)

        assert zip_path == (tmp_path / "public.zip").resolve()
        with zipfile.ZipFile(zip_path) as archive:
            assert sorted(archive.namelist()) == ["images/corgi.txt", "index.html"]
            assert archive.read("images/corgi.txt") == b"woof"
