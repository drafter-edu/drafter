"""Tests for the site-wide page transition setting.

`set_page_transition()` configures a visual transition that plays whenever
the user navigates between pages: "fade" fades the new page in from
transparent, while any CSS color (e.g. "black", "white") fades it in from a
solid veil of that color. The animation itself is CSS (drafter_base.css);
the bridge restarts it on the body container after each navigation swap.
These tests cover the configuration pipeline (defaults, environment
variables, CLI parsing, serialization, copying), the deploy-time API's
normalization, and the SiteRenderer's class/custom-property application.
"""

import argparse
import sys
from unittest.mock import MagicMock

import pytest

from drafter.config.client_server import ClientServerConfiguration

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.site_renderer import (
    PAGE_TRANSITION_FADE_CLASS,
    PAGE_TRANSITION_VEIL_CLASS,
    SiteRenderer,
)
from drafter.deploy import set_page_transition
from drafter.site.site import DRAFTER_TAG_IDS


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    ClientServerConfiguration.extend_parser(parser)
    return parser


class TestPageTransitionDefaults:
    def test_default_is_none(self):
        config = ClientServerConfiguration()
        assert config.page_transition == "none"
        assert config.page_transition_duration == 0.5

    def test_to_json_includes_page_transition(self):
        config = ClientServerConfiguration(
            page_transition="fade", page_transition_duration=1.25
        )
        as_json = config.to_json()
        assert as_json["page_transition"] == "fade"
        assert as_json["page_transition_duration"] == 1.25

    def test_copy_preserves_page_transition(self):
        config = ClientServerConfiguration(
            page_transition="black", page_transition_duration=0.75
        )
        copied = config.copy()
        assert copied.page_transition == "black"
        assert copied.page_transition_duration == 0.75


class TestPageTransitionEnvVars:
    def test_env_vars_parsed(self):
        result = ClientServerConfiguration.parse_env_variables(
            {
                "DRAFTER_PAGE_TRANSITION": "white",
                "DRAFTER_PAGE_TRANSITION_DURATION": "0.25",
            }
        )
        assert result["page_transition"] == "white"
        assert result["page_transition_duration"] == 0.25

    def test_env_vars_absent(self):
        result = ClientServerConfiguration.parse_env_variables({})
        assert "page_transition" not in result
        assert "page_transition_duration" not in result

    def test_invalid_duration_skipped(self):
        result = ClientServerConfiguration.parse_env_variables(
            {"DRAFTER_PAGE_TRANSITION_DURATION": "fast"}
        )
        assert "page_transition_duration" not in result


class TestPageTransitionCli:
    @pytest.mark.parametrize("transition", ["none", "fade", "black", "#004488"])
    def test_page_transition_flag(self, transition):
        parser = make_parser()
        parsed, _ = parser.parse_known_args(["--page-transition", transition])
        result = ClientServerConfiguration.parse_args(vars(parsed))
        assert result["page_transition"] == transition

    def test_duration_flag(self):
        parser = make_parser()
        parsed, _ = parser.parse_known_args(["--page-transition-duration", "1.5"])
        result = ClientServerConfiguration.parse_args(vars(parsed))
        assert result["page_transition_duration"] == 1.5

    def test_flags_not_given(self):
        parser = make_parser()
        parsed, _ = parser.parse_known_args([])
        result = ClientServerConfiguration.parse_args(vars(parsed))
        assert "page_transition" not in result
        assert "page_transition_duration" not in result

    def test_merges_into_configuration(self):
        parser = make_parser()
        parsed, _ = parser.parse_known_args(
            ["--page-transition", "fade", "--page-transition-duration", "2"]
        )
        config = ClientServerConfiguration()
        config.merge_in_args(ClientServerConfiguration.parse_args(vars(parsed)), False)
        assert config.page_transition == "fade"
        assert config.page_transition_duration == 2.0


class TestSetPageTransition:
    def make_server(self):
        server = MagicMock()
        server.settings = {}
        server.reconfigure = lambda **kwargs: server.settings.update(kwargs)
        return server

    def test_default_is_fade(self):
        server = self.make_server()
        set_page_transition(server=server)
        assert server.settings == {"page_transition": "fade"}

    def test_none_disables(self):
        server = self.make_server()
        set_page_transition(None, server=server)
        assert server.settings == {"page_transition": "none"}

    def test_transparent_normalizes_to_fade(self):
        server = self.make_server()
        set_page_transition("transparent", server=server)
        assert server.settings == {"page_transition": "fade"}

    def test_color_and_duration(self):
        server = self.make_server()
        set_page_transition("black", duration=1, server=server)
        assert server.settings == {
            "page_transition": "black",
            "page_transition_duration": 1.0,
        }


### Minimal fake DOM for the renderer's class/custom-property application


class FakeClassList:
    def __init__(self):
        self.names: list[str] = []

    def add(self, *names):
        for name in names:
            if name not in self.names:
                self.names.append(name)

    def remove(self, *names):
        self.names = [name for name in self.names if name not in names]


class FakeStyle:
    def __init__(self):
        self.properties: dict[str, str] = {}

    def setProperty(self, name, value):
        self.properties[name] = value


class FakeBodyElement:
    def __init__(self):
        self.classList = FakeClassList()
        self.style = FakeStyle()
        self.offsetWidth = 0


class FakeScope:
    def __init__(self, body):
        self.body = body

    def querySelector(self, selector):
        if selector == "#" + DRAFTER_TAG_IDS["BODY"]:
            return self.body
        return None


def make_renderer(body=None):
    runtime = MagicMock()
    renderer = SiteRenderer(runtime, "root", "root")
    renderer.scope = FakeScope(body)
    return renderer


class TestApplyPageTransition:
    def test_none_leaves_body_untouched(self):
        body = FakeBodyElement()
        make_renderer(body).apply_page_transition("none", 0.5)
        assert body.classList.names == []
        assert body.style.properties == {}

    def test_fade_adds_class_and_duration(self):
        body = FakeBodyElement()
        make_renderer(body).apply_page_transition("fade", 0.5)
        assert body.classList.names == [PAGE_TRANSITION_FADE_CLASS]
        assert body.style.properties == {"--drafter-page-transition-duration": "0.5s"}

    def test_color_adds_veil_class_and_color(self):
        body = FakeBodyElement()
        make_renderer(body).apply_page_transition("black", 1.0)
        assert body.classList.names == [PAGE_TRANSITION_VEIL_CLASS]
        assert body.style.properties == {
            "--drafter-page-transition-duration": "1.0s",
            "--drafter-page-transition-color": "black",
        }

    def test_reapplying_restarts_animation(self):
        body = FakeBodyElement()
        renderer = make_renderer(body)
        renderer.apply_page_transition("black", 0.5)
        renderer.apply_page_transition("fade", 0.5)
        assert body.classList.names == [PAGE_TRANSITION_FADE_CLASS]

    def test_missing_body_is_harmless(self):
        make_renderer(body=None).apply_page_transition("fade", 0.5)
