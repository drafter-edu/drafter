"""Tests for the website favicon setting.

The favicon flows through the standard configuration pipeline: a `favicon`
field on both AppCommonConfiguration (read by the index template at
serve/build time via the `--favicon` CLI flag or `DRAFTER_FAVICON`) and
ClientServerConfiguration (updated by `set_website_favicon()` and applied to
the live document by the ClientBridge). When no favicon is configured, the
index template inlines the built-in Drafter icon as an SVG data URI, so every
Drafter site gets a favicon without any served asset path. These tests cover
the configuration pipeline (defaults, environment variables, CLI parsing,
serialization, copying), the deploy-time API, the template rendering, and the
DOM helper that swaps the favicon link.
"""

import argparse
import sys
from unittest.mock import MagicMock

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.dom import set_favicon
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.system import SystemConfiguration
from drafter.deploy import set_website_favicon
from drafter.scaffolding.templating import (
    default_favicon_data_uri,
    render_index_html,
)
from drafter.site.initial_site_data import InitialSiteData
from drafter.site.site import DRAFTER_TAG_IDS


def make_system() -> SystemConfiguration:
    return SystemConfiguration(
        bootstrap=BootstrapConfiguration(path="main.py"),
        client_server=ClientServerConfiguration(),
        app_server=AppServerConfiguration(),
        app_builder=AppBuilderConfiguration(),
        app_common=AppCommonConfiguration(),
    )


class TestFaviconDefaults:
    def test_default_is_empty(self):
        assert ClientServerConfiguration().favicon == ""
        assert AppCommonConfiguration().favicon == ""

    def test_to_json_includes_favicon(self):
        config = ClientServerConfiguration(favicon="icon.png")
        assert config.to_json()["favicon"] == "icon.png"

    def test_copy_preserves_favicon(self):
        config = ClientServerConfiguration(favicon="icon.png")
        assert config.copy().favicon == "icon.png"

    def test_update_configuration_sets_favicon(self):
        config = ClientServerConfiguration()
        config.update_configuration("favicon", "icon.png")
        assert config.favicon == "icon.png"

    def test_initial_site_data_default(self):
        data = InitialSiteData(site_html="", site_title="Title")
        assert data.favicon == ""


class TestFaviconEnvVars:
    def test_env_var_parsed_by_both_sections(self):
        env = {"DRAFTER_FAVICON": "icon.svg"}
        assert ClientServerConfiguration.parse_env_variables(env)["favicon"] == (
            "icon.svg"
        )
        assert AppCommonConfiguration.parse_env_variables(env)["favicon"] == (
            "icon.svg"
        )

    def test_env_var_absent(self):
        assert "favicon" not in ClientServerConfiguration.parse_env_variables({})
        assert "favicon" not in AppCommonConfiguration.parse_env_variables({})


class TestFaviconCli:
    def make_parser(self) -> argparse.ArgumentParser:
        # The --favicon flag is registered by app_common (like --site-title),
        # but both sections read the parsed value.
        parser = argparse.ArgumentParser()
        AppCommonConfiguration.extend_parser(parser)
        return parser

    def test_favicon_flag(self):
        parsed, _ = self.make_parser().parse_known_args(["--favicon", "icon.png"])
        assert AppCommonConfiguration.parse_args(vars(parsed))["favicon"] == "icon.png"
        assert ClientServerConfiguration.parse_args(vars(parsed))["favicon"] == (
            "icon.png"
        )

    def test_flag_not_given(self):
        parsed, _ = self.make_parser().parse_known_args([])
        assert "favicon" not in AppCommonConfiguration.parse_args(vars(parsed))
        assert "favicon" not in ClientServerConfiguration.parse_args(vars(parsed))

    def test_merges_into_configuration(self):
        parsed, _ = self.make_parser().parse_known_args(["--favicon", "icon.png"])
        config = AppCommonConfiguration()
        config.merge_in_args(AppCommonConfiguration.parse_args(vars(parsed)), False)
        assert config.favicon == "icon.png"


class TestSetWebsiteFavicon:
    def test_reconfigures_server(self):
        server = MagicMock()
        set_website_favicon("icon.png", server=server)
        server.reconfigure.assert_called_once_with(favicon="icon.png")


class TestFaviconTemplate:
    def render(self, system: SystemConfiguration) -> str:
        return render_index_html(
            system=system,
            modified_system={},
            inline_py=True,
            user_code="",
            python_url=None,
            dev_ws_url=None,
            assets_url="assets",
        )

    def test_default_favicon_is_inlined_data_uri(self):
        html = self.render(make_system())
        assert f'id="{DRAFTER_TAG_IDS["FAVICON"]}"' in html
        assert 'href="data:image/svg+xml;base64,' in html

    def test_configured_favicon_used_verbatim(self):
        system = make_system()
        system.app_common.favicon = "my_icon.png"
        html = self.render(system)
        assert 'href="my_icon.png"' in html
        assert "data:image/svg+xml" not in html

    def test_default_data_uri_encodes_scaffolding_svg(self):
        uri = default_favicon_data_uri()
        assert uri.startswith("data:image/svg+xml;base64,")
        # A data URI is only useful if it holds the actual SVG payload.
        import base64

        decoded = base64.b64decode(uri.split(",", 1)[1])
        assert b"<svg" in decoded


class TestSetFaviconDomHelper:
    def test_updates_existing_link(self):
        document = MagicMock()
        link = MagicMock()
        document.getElementById.return_value = link
        set_favicon(document, "icon.png")
        document.getElementById.assert_called_once_with(DRAFTER_TAG_IDS["FAVICON"])
        link.setAttribute.assert_called_once_with("href", "icon.png")
        document.createElement.assert_not_called()

    def test_creates_link_when_missing(self):
        document = MagicMock()
        document.getElementById.return_value = None
        set_favicon(document, "icon.png")
        link = document.createElement.return_value
        document.createElement.assert_called_once_with("link")
        link.setAttribute.assert_any_call("rel", "icon")
        link.setAttribute.assert_any_call("id", DRAFTER_TAG_IDS["FAVICON"])
        link.setAttribute.assert_any_call("href", "icon.png")
        document.head.appendChild.assert_called_once_with(link)
