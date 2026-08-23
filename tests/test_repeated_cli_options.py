"""Tests for the repeatable list-valued CLI options.

List-valued settings used to be passed as a single semicolon-separated
argument; they are now given by repeating the flag once per entry. The
DRAFTER_* environment variables remain semicolon-separated, since an
environment variable cannot be repeated.
"""

import argparse

from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_common import AppCommonConfiguration
from drafter.config.client_server import ClientServerConfiguration


def parse(configuration_class, argv):
    parser = argparse.ArgumentParser()
    configuration_class.extend_parser(parser)
    parsed, _ = parser.parse_known_args(argv)
    return configuration_class.parse_args(vars(parsed))


class TestClientServerRepeatedOptions:
    def test_external_pages_repeated(self):
        result = parse(
            ClientServerConfiguration,
            [
                "--external-pages",
                "https://example.com Docs",
                "--external-pages",
                "https://example.org",
            ],
        )
        assert result["external_pages"] == [
            "https://example.com Docs",
            "https://example.org",
        ]

    def test_additional_content_repeated(self):
        result = parse(
            ClientServerConfiguration,
            [
                "--additional-css-content",
                "https://example.com/a.css",
                "--additional-css-content",
                " https://example.com/b.css ",
                "--additional-js-content",
                "console.log('hi');",
            ],
        )
        assert result["additional_css_content"] == [
            "https://example.com/a.css",
            "https://example.com/b.css",
        ]
        assert result["additional_js_content"] == ["console.log('hi');"]

    def test_semicolons_no_longer_split(self):
        # A semicolon inside a single value is preserved verbatim, which
        # matters for inline CSS/JS where semicolons are ordinary syntax.
        result = parse(
            ClientServerConfiguration,
            ["--additional-style-content", "body { color: red; margin: 0; }"],
        )
        assert result["additional_style_content"] == ["body { color: red; margin: 0; }"]

    def test_not_given_is_absent(self):
        result = parse(ClientServerConfiguration, [])
        assert "external_pages" not in result
        assert "additional_header_content" not in result

    def test_env_vars_still_semicolon_separated(self):
        result = ClientServerConfiguration.parse_env_variables(
            {"DRAFTER_EXTERNAL_PAGES": "https://a.com;https://b.com"}
        )
        assert result["external_pages"] == ["https://a.com", "https://b.com"]


class TestAppCommonRepeatedOptions:
    def test_packages_repeated(self):
        result = parse(
            AppCommonConfiguration,
            [
                "--project-packages",
                "wordfreq",
                "--project-packages",
                "emoji",
                "--system-packages",
                "bakery",
            ],
        )
        assert result["project_packages"] == ["wordfreq", "emoji"]
        assert result["system_packages"] == ["bakery"]

    def test_not_given_is_absent(self):
        result = parse(AppCommonConfiguration, [])
        assert "project_packages" not in result
        assert "system_packages" not in result

    def test_env_vars_still_semicolon_separated(self):
        result = AppCommonConfiguration.parse_env_variables(
            {"DRAFTER_PROJECT_PACKAGES": "wordfreq;emoji"}
        )
        assert result["project_packages"] == ["wordfreq", "emoji"]


class TestAppBuilderRepeatedOptions:
    def test_additional_paths_repeated(self):
        result = parse(
            AppBuilderConfiguration,
            [
                "--additional-paths",
                "pets.csv",
                "--additional-paths",
                "words.txt",
            ],
        )
        assert result["additional_paths"] == ["pets.csv", "words.txt"]

    def test_not_given_is_absent(self):
        result = parse(AppBuilderConfiguration, [])
        assert "additional_paths" not in result

    def test_env_vars_still_semicolon_separated(self):
        result = AppBuilderConfiguration.parse_env_variables(
            {"DRAFTER_ADDITIONAL_PATHS": "pets.csv;words.txt"}
        )
        assert result["additional_paths"] == ["pets.csv", "words.txt"]
