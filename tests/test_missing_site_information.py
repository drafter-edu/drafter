"""Tests for the missing-site-information notice printed by the builder.

Covers drafter-edu/drafter#183: building a site that never called
`set_site_information` prints a notice (the build still succeeds), and the
`warn_missing_info` setting, which used to be accepted and ignored, now
controls it from every configuration source.
"""

import argparse
from pathlib import Path

import pytest

from drafter import set_site_information
from drafter.builder.build import (
    MISSING_SITE_INFORMATION_NOTICE,
    compile_site,
    has_site_information,
    warn_if_site_information_missing,
)
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

NOTICE_START = "Notice: this site has no site information."
ANNOTATION_START = "::warning title=Drafter site information missing::"


def make_system(tmp_path: Path, warn_missing_info: bool = True) -> SystemConfiguration:
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
            warn_missing_info=warn_missing_info,
        ),
        app_common=AppCommonConfiguration(
            prerender_initial_page=False, asset_directory=str(assets)
        ),
    )


def make_server(with_information: bool) -> ClientServer:
    """A server that has not started, as it is when the builder runs."""
    server = ClientServer(custom_name="SITE_INFORMATION_TEST")
    if with_information:
        set_site_information(
            author="Your Name",
            description="Order snacks for very good dogs.",
            sources="",
            planning="",
            links=[],
            server=server,
        )
    return server


@pytest.fixture(autouse=True)
def fresh_defaults(tmp_path, monkeypatch):
    """Give each test its own default configuration.

    Before a server starts, `set_site_information` writes into the
    system-wide defaults, so without this one test's site information
    would still be set in the next test.
    """
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    _set_system_for_testing(make_system(tmp_path))
    yield
    _reset_system_for_testing()


class TestHasSiteInformation:
    def test_false_when_never_set(self):
        assert has_site_information(make_server(with_information=False)) is False

    def test_true_once_any_field_is_filled(self):
        assert has_site_information(make_server(with_information=True)) is True

    def test_false_when_every_field_is_empty(self):
        server = ClientServer(custom_name="SITE_INFORMATION_EMPTY")
        set_site_information("", "", [], [], [], server=server)

        assert has_site_information(server) is False


class TestNotice:
    def test_printed_when_information_is_missing(self, tmp_path, capsys):
        printed = warn_if_site_information_missing(
            make_system(tmp_path), make_server(with_information=False)
        )

        assert printed is True
        output = capsys.readouterr().out
        assert MISSING_SITE_INFORMATION_NOTICE in output
        assert "set_site_information(" in output
        assert "--no-warn-missing-info" in output

    def test_silent_when_information_is_set(self, tmp_path, capsys):
        printed = warn_if_site_information_missing(
            make_system(tmp_path), make_server(with_information=True)
        )

        assert printed is False
        assert capsys.readouterr().out == ""

    def test_silent_when_the_setting_is_off(self, tmp_path, capsys):
        printed = warn_if_site_information_missing(
            make_system(tmp_path, warn_missing_info=False),
            make_server(with_information=False),
        )

        assert printed is False
        assert capsys.readouterr().out == ""

    def test_no_github_annotation_outside_github_actions(self, tmp_path, capsys):
        warn_if_site_information_missing(
            make_system(tmp_path), make_server(with_information=False)
        )

        assert ANNOTATION_START not in capsys.readouterr().out

    def test_github_annotation_inside_github_actions(
        self, tmp_path, capsys, monkeypatch
    ):
        monkeypatch.setenv("GITHUB_ACTIONS", "true")

        warn_if_site_information_missing(
            make_system(tmp_path), make_server(with_information=False)
        )

        annotations = [
            line
            for line in capsys.readouterr().out.splitlines()
            if line.startswith(ANNOTATION_START)
        ]
        assert len(annotations) == 1
        assert "set_site_information" in annotations[0]


class TestCompileSite:
    def test_build_succeeds_and_prints_the_notice(self, tmp_path, capsys):
        compile_site(make_system(tmp_path), make_server(with_information=False), None)

        assert (tmp_path / "dist" / "index.html").exists()
        assert NOTICE_START in capsys.readouterr().out

    def test_build_with_information_prints_no_notice(self, tmp_path, capsys):
        compile_site(make_system(tmp_path), make_server(with_information=True), None)

        assert (tmp_path / "dist" / "index.html").exists()
        assert NOTICE_START not in capsys.readouterr().out

    def test_build_with_the_setting_off_prints_no_notice(self, tmp_path, capsys):
        compile_site(
            make_system(tmp_path, warn_missing_info=False),
            make_server(with_information=False),
            None,
        )

        assert NOTICE_START not in capsys.readouterr().out


class TestSettingSources:
    def parse(self, *argv: str) -> dict:
        parser = argparse.ArgumentParser()
        AppBuilderConfiguration.extend_parser(parser)
        return AppBuilderConfiguration.parse_args(vars(parser.parse_args(argv)))

    def test_default_is_on(self):
        assert AppBuilderConfiguration().warn_missing_info is True

    def test_no_flag_leaves_other_sources_alone(self):
        assert "warn_missing_info" not in self.parse()

    def test_flag_turns_it_off(self):
        assert self.parse("--no-warn-missing-info") == {"warn_missing_info": False}

    def test_flag_turns_it_on(self):
        assert self.parse("--warn-missing-info") == {"warn_missing_info": True}

    def test_environment_variable_turns_it_off(self):
        parsed = AppBuilderConfiguration.parse_env_variables(
            {"DRAFTER_WARN_MISSING_INFO": "false"}
        )

        assert parsed == {"warn_missing_info": False}
