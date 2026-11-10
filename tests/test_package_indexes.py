"""Tests for the wheel index settings: which `wheels.json` URLs the browser
searches when a package or one of its dependencies has no wheel on PyPI."""

from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import DEFAULT_PACKAGE_INDEX, AppCommonConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.configuration import get_system_config_modifications
from drafter.scaffolding.templating import render_index_html

EXTRA = "https://course.example/wheels/wheels.json"


class TestGetPackageIndexes:
    def test_default_is_drafters_own_index(self):
        assert AppCommonConfiguration().get_package_indexes() == [DEFAULT_PACKAGE_INDEX]

    def test_extra_indexes_come_first_then_the_default(self):
        config = AppCommonConfiguration(package_indexes=[EXTRA])

        assert config.get_package_indexes() == [EXTRA, DEFAULT_PACKAGE_INDEX]

    def test_default_can_be_turned_off(self):
        config = AppCommonConfiguration(
            package_indexes=[EXTRA], use_default_package_index=False
        )

        assert config.get_package_indexes() == [EXTRA]

    def test_blank_and_repeated_entries_are_dropped(self):
        config = AppCommonConfiguration(
            package_indexes=[EXTRA, " ", EXTRA, DEFAULT_PACKAGE_INDEX]
        )

        assert config.get_package_indexes() == [EXTRA, DEFAULT_PACKAGE_INDEX]

    def test_default_index_names_a_json_file(self):
        assert DEFAULT_PACKAGE_INDEX.startswith("https://")
        assert DEFAULT_PACKAGE_INDEX.endswith("/wheels.json")


class TestPageTemplate:
    """The browser learns the indexes from the page Drafter renders."""

    def render(self, shared_runtime: bool = False, **common) -> str:
        system = SystemConfiguration(
            bootstrap=BootstrapConfiguration(path="main.py"),
            client_server=ClientServerConfiguration(),
            app_server=AppServerConfiguration(),
            app_builder=AppBuilderConfiguration(shared_runtime=shared_runtime),
            app_common=AppCommonConfiguration(**common),
        )
        return render_index_html(
            system=system,
            modified_system=get_system_config_modifications(),
            inline_py=True,
            user_code="from drafter import *\nstart_server()\n",
            python_url="main.py",
            assets_url="assets",
            dev_ws_url=None,
            compiled_body="",
            compiled_headers="",
            pyodide_drafter_path="drafter==0.0.0",
        )

    def test_indexes_reach_the_standalone_boot_path(self):
        html = self.render(package_indexes=[EXTRA])

        expected = f'packageIndexes: ["{EXTRA}", "{DEFAULT_PACKAGE_INDEX}"]'
        assert html.count(expected) == 1

    def test_indexes_reach_the_embedded_boot_path_too(self):
        html = self.render(shared_runtime=True, package_indexes=[EXTRA])

        expected = f'packageIndexes: ["{EXTRA}", "{DEFAULT_PACKAGE_INDEX}"]'
        # Once for the host-attached path, once for the standalone fallback.
        assert html.count(expected) == 2

    def test_without_the_default_only_the_extras_are_passed(self):
        html = self.render(package_indexes=[EXTRA], use_default_package_index=False)

        assert f'packageIndexes: ["{EXTRA}"]' in html
        assert DEFAULT_PACKAGE_INDEX not in html
