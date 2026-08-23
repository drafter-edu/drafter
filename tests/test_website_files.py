"""Tests for linking files into every page of a site.

`add_website_css_file()`, `add_website_js_file()`, `add_website_js()`, and
`add_website_file()` in `drafter.deploy` register stylesheets, scripts, and
other files that a site needs. Files next to the student's program are
validated up front by `drafter.files.website_files`: a missing file raises a
`StudentFacingError` that suggests similarly named files (a capitalization
slip, a different extension, a typo, or the same name in a subfolder). The
registered files flow through three new list-valued configuration keys
(`additional_css_files`, `additional_js_files`, `additional_files`), are
linked verbatim by the site renderer (no assets-folder remapping), and are
copied into the built site by `copy_adjacent_file`.
"""

import argparse
import json
import pathlib
import sys
from unittest.mock import MagicMock

import pytest

from drafter.client_server.client_server import ClientServer
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.urls import INTERNAL_ROUTES, is_absolute_url
from drafter.configuration import get_system_configuration
from drafter.data.errors import StudentFacingError
from drafter.deploy import (
    add_website_css,
    add_website_css_file,
    add_website_file,
    add_website_js,
    add_website_js_file,
)
from drafter.files import website_files
from drafter.files.website_files import (
    WebsiteFileLookup,
    find_in_subfolders,
    find_similar_files,
    is_url,
    list_directory_entries,
    looks_like_code,
    lookup_website_file,
    missing_file_error,
    normalize_website_path,
    resolve_website_file,
)
from drafter.site.site import Site

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter.bridge.dom import add_script_link
from drafter.builder.build import copy_adjacent_file


@pytest.fixture
def program_dir(tmp_path, monkeypatch):
    """A fake student folder, made the configured user directory."""
    (tmp_path / "main.py").write_text("print('hi')")
    (tmp_path / "styles.css").write_text("h1 { color: red; }")
    (tmp_path / "app.js").write_text("console.log('hi');")
    (tmp_path / "words.txt").write_text("apple\nbanana\n")
    (tmp_path / "Logo.PNG").write_bytes(b"png")
    static = tmp_path / "static"
    static.mkdir()
    (static / "style.css").write_text("body {}")
    (static / "extra.js").write_text("")
    monkeypatch.setattr(
        get_system_configuration().bootstrap, "path", str(tmp_path / "main.py")
    )
    return tmp_path


@pytest.fixture
def server():
    """A fresh, unstarted ClientServer.

    Before `start_server`, reconfigure() writes to the shared system
    configuration, so its list-valued keys are cleared around each test.
    """
    system_config = get_system_configuration().client_server
    for key in ClientServerConfiguration.LIST_CONTENT_KEYS:
        setattr(system_config, key, [])
    yield ClientServer("test_website_files")
    for key in ClientServerConfiguration.LIST_CONTENT_KEYS:
        setattr(system_config, key, [])


# ============================================================================
# CONFIGURATION PIPELINE
# ============================================================================


class TestConfiguration:
    def test_defaults_are_empty_lists(self):
        config = ClientServerConfiguration()
        assert config.additional_css_files == []
        assert config.additional_js_files == []
        assert config.additional_files == []

    def test_list_content_keys_include_new_fields(self):
        keys = ClientServerConfiguration.LIST_CONTENT_KEYS
        assert "additional_css_files" in keys
        assert "additional_js_files" in keys
        assert "additional_files" in keys
        # The pre-existing keys are still there.
        assert "additional_style_content" in keys

    def test_update_configuration_appends(self):
        config = ClientServerConfiguration()
        config.update_configuration("additional_css_files", "a.css")
        config.update_configuration("additional_css_files", "b.css")
        config.update_configuration("additional_files", "words.txt")
        assert config.additional_css_files == ["a.css", "b.css"]
        assert config.additional_files == ["words.txt"]

    def test_to_json_and_copy(self):
        config = ClientServerConfiguration(
            additional_css_files=["a.css"],
            additional_js_files=["a.js"],
            additional_files=["a.css", "a.js", "data.csv"],
        )
        as_json = config.to_json()
        assert as_json["additional_css_files"] == ["a.css"]
        assert as_json["additional_js_files"] == ["a.js"]
        assert as_json["additional_files"] == ["a.css", "a.js", "data.csv"]
        copied = config.copy()
        assert copied.additional_files == config.additional_files
        assert copied.additional_files is not config.additional_files

    def test_env_vars(self):
        env = {
            "DRAFTER_ADDITIONAL_CSS_FILES": "a.css;b.css",
            "DRAFTER_ADDITIONAL_JS_FILES": "a.js",
            "DRAFTER_ADDITIONAL_FILES": "words.txt;images/logo.png",
        }
        parsed = ClientServerConfiguration.parse_env_variables(env)
        assert parsed["additional_css_files"] == ["a.css", "b.css"]
        assert parsed["additional_js_files"] == ["a.js"]
        assert parsed["additional_files"] == ["words.txt", "images/logo.png"]

    def test_cli_flags_repeat(self):
        parser = argparse.ArgumentParser()
        ClientServerConfiguration.extend_parser(parser)
        args = parser.parse_args(
            [
                "--additional-css-files",
                "a.css",
                "--additional-css-files",
                "b.css",
                "--additional-js-files",
                "a.js",
                "--additional-files",
                "words.txt",
            ]
        )
        parsed = ClientServerConfiguration.parse_args(vars(args))
        assert parsed["additional_css_files"] == ["a.css", "b.css"]
        assert parsed["additional_js_files"] == ["a.js"]
        assert parsed["additional_files"] == ["words.txt"]


# ============================================================================
# PATH HELPERS
# ============================================================================


class TestPathHelpers:
    @pytest.mark.parametrize(
        "path,expected",
        [
            ("https://example.com/style.css", True),
            ("http://example.com/style.css", True),
            ("//cdn.example.com/style.css", True),
            ("data:text/css,body{}", True),
            ("style.css", False),
            ("static/style.css", False),
        ],
    )
    def test_is_url(self, path, expected):
        assert is_url(path) is expected

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://example.com/a.css", True),
            ("//cdn/a.css", True),
            ("/a.css", True),
            ("data:text/css,", True),
            ("a.css", False),
            ("themes/a.css", False),
        ],
    )
    def test_is_absolute_url(self, url, expected):
        assert is_absolute_url(url) is expected

    def test_normalize_website_path(self):
        assert normalize_website_path(r".\static\style.css") == "static/style.css"
        assert normalize_website_path("  style.css ") == "style.css"
        assert normalize_website_path("././a/b.css") == "a/b.css"

    def test_looks_like_code(self):
        assert looks_like_code("h1 { color: red; }")
        assert looks_like_code("color: red;")
        assert looks_like_code("line one\nline two")
        assert not looks_like_code("style.css")
        assert not looks_like_code("static/my style.css")


class TestSimilarFiles:
    def test_capitalization_first(self):
        found = find_similar_files("logo.png", ["Logo.PNG", "logo.svg", "logos.png"])
        assert found[0] == "Logo.PNG"

    def test_same_stem_different_extension(self):
        found = find_similar_files("style.css", ["style.scss", "readme.md"])
        assert found == ["style.scss"]

    def test_typo(self):
        found = find_similar_files("style.css", ["styles.css", "main.py"])
        assert found == ["styles.css"]

    def test_never_suggests_itself_or_duplicates(self):
        found = find_similar_files("style.css", ["style.css", "Style.css", "Style.css"])
        assert found == ["Style.css"]

    def test_limits_suggestions(self):
        candidates = [f"style{i}.css" for i in range(10)]
        assert len(find_similar_files("style.css", candidates)) == 3

    def test_nothing_similar(self):
        assert find_similar_files("style.css", ["main.py", "data.csv"]) == []

    def test_find_in_subfolders(self, program_dir):
        assert find_in_subfolders(program_dir, "style.css") == ["static/style.css"]
        assert find_in_subfolders(program_dir, "STYLE.CSS") == ["static/style.css"]
        assert find_in_subfolders(program_dir, "nothing.css") == []

    def test_find_in_subfolders_skips_hidden_and_tool_folders(self, program_dir):
        for folder in (".git", "node_modules", "_private"):
            (program_dir / folder).mkdir()
            (program_dir / folder / "hidden.css").write_text("")
        assert find_in_subfolders(program_dir, "hidden.css") == []

    def test_list_directory_entries_marks_folders(self, program_dir):
        entries = list_directory_entries(program_dir)
        assert "static/" in entries
        assert "styles.css" in entries
        assert list_directory_entries(program_dir / "missing") == []


# ============================================================================
# LOOKUP AND RESOLUTION (NATIVE)
# ============================================================================


class TestLookupNative:
    def test_existing_file(self, program_dir):
        lookup = lookup_website_file("styles.css")
        assert lookup.exists is True
        assert lookup.searched_in == str(program_dir)

    def test_missing_file_reports_siblings_and_subfolders(self, program_dir):
        lookup = lookup_website_file("style.css")
        assert lookup.exists is False
        assert "styles.css" in lookup.siblings
        assert lookup.in_subfolders == ["static/style.css"]

    def test_missing_file_in_subfolder_lists_that_subfolder(self, program_dir):
        lookup = lookup_website_file("static/styles.css")
        assert lookup.exists is False
        assert "style.css" in lookup.siblings

    def test_falls_back_to_cwd_without_bootstrap_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr(get_system_configuration().bootstrap, "path", None)
        monkeypatch.chdir(tmp_path)
        (tmp_path / "here.css").write_text("")
        assert lookup_website_file("here.css").exists is True
        assert lookup_website_file("gone.css").exists is False


class TestResolveWebsiteFile:
    def test_urls_pass_through_untouched(self, program_dir):
        url = "https://fonts.googleapis.com/css2?family=Lora"
        assert resolve_website_file(url, "add_website_css_file", "css") == url
        assert resolve_website_file(" //cdn/x.js ", "add_website_js_file", "js") == (
            "//cdn/x.js"
        )

    def test_local_file_is_normalized(self, program_dir):
        assert (
            resolve_website_file(r".\static\style.css", "add_website_css_file", "css")
            == "static/style.css"
        )

    def test_missing_file_error_suggests_similar(self, program_dir):
        with pytest.raises(StudentFacingError) as info:
            resolve_website_file("style.css", "add_website_css_file", "css")
        error = info.value
        assert "style.css" in str(error)
        assert error.friendly_title == "Website File Not Found"
        assert str(program_dir) in error.friendly_message
        assert "styles.css" in error.friendly_message
        assert "Did you mean 'styles.css'?" in error.friendly_steps
        assert any("static/style.css" in step for step in error.friendly_steps)

    def test_missing_file_in_subfolder_prefixes_suggestions(self, program_dir):
        with pytest.raises(StudentFacingError) as info:
            resolve_website_file("static/styles.css", "add_website_css_file", "css")
        assert "Did you mean 'static/style.css'?" in info.value.friendly_steps

    def test_missing_file_without_similar_names(self, program_dir):
        with pytest.raises(StudentFacingError) as info:
            resolve_website_file("zzz.css", "add_website_css_file", "css")
        assert "Similar names" not in info.value.friendly_message
        assert not any("Did you mean" in s for s in info.value.friendly_steps)

    def test_capitalization_mismatch_is_suggested(self):
        # Built directly, since case-insensitive filesystems (Windows, macOS)
        # would happily find "logo.png" when only "Logo.PNG" exists.
        lookup = WebsiteFileLookup()
        lookup.siblings = ["Logo.PNG", "main.py"]
        error = missing_file_error("add_website_file", "logo.png", lookup)
        assert "Did you mean 'Logo.PNG'?" in error.friendly_steps
        assert error.friendly_title == "Website File Not Found"

    @pytest.mark.parametrize("bad", [5, None, ["style.css"]])
    def test_non_string(self, program_dir, bad):
        with pytest.raises(StudentFacingError) as info:
            resolve_website_file(bad, "add_website_css_file", "css")
        assert info.value.friendly_title == "Website File Path Must Be a String"

    def test_empty_string(self, program_dir):
        with pytest.raises(StudentFacingError) as info:
            resolve_website_file("   ", "add_website_file", "file")
        assert info.value.friendly_title == "Website File Path Is Empty"

    def test_code_instead_of_name(self, program_dir):
        with pytest.raises(StudentFacingError) as info:
            resolve_website_file("h1 { color: red; }", "add_website_css_file", "css")
        assert info.value.friendly_title == "CSS Code Given Instead of a File"
        assert any("add_website_css(" in step for step in info.value.friendly_steps)

        with pytest.raises(StudentFacingError) as info:
            resolve_website_file("alert(1);", "add_website_js_file", "js")
        assert info.value.friendly_title == "JavaScript Code Given Instead of a File"

    @pytest.mark.parametrize("path", [r"C:\Users\ada\style.css", "/etc/style.css"])
    def test_absolute_path(self, program_dir, path):
        with pytest.raises(StudentFacingError) as info:
            resolve_website_file(path, "add_website_css_file", "css")
        assert info.value.friendly_title == "Website File Must Be Next to Your Program"
        assert "absolute" in str(info.value)

    def test_parent_escape(self, program_dir):
        with pytest.raises(StudentFacingError) as info:
            resolve_website_file("../styles.css", "add_website_css_file", "css")
        assert info.value.friendly_title == "Website File Must Be Next to Your Program"
        assert "leaves the program folder" in str(info.value)

    def test_wrong_extension(self, program_dir):
        with pytest.raises(StudentFacingError) as info:
            resolve_website_file("words.txt", "add_website_css_file", "css")
        assert info.value.friendly_title == "Not a CSS File"
        with pytest.raises(StudentFacingError) as info:
            resolve_website_file("styles.css", "add_website_js_file", "js")
        assert info.value.friendly_title == "Not a JavaScript File"

    def test_extension_is_case_insensitive(self, program_dir):
        (program_dir / "SHOUT.CSS").write_text("")
        assert resolve_website_file("SHOUT.CSS", "add_website_css_file", "css") == (
            "SHOUT.CSS"
        )

    def test_generic_files_accept_any_extension(self, program_dir):
        assert resolve_website_file("words.txt", "add_website_file") == "words.txt"
        assert resolve_website_file("Logo.PNG", "add_website_file") == "Logo.PNG"


# ============================================================================
# LOOKUP IN PYODIDE (SIMULATED)
# ============================================================================


class FakeXHR:
    """Stand-in for the browser's synchronous XMLHttpRequest."""

    responses: dict = {}
    requests: list = []

    def __init__(self):
        self.status = 0
        self.responseText = ""
        self._method = ""
        self._url = ""

    @classmethod
    def new(cls):
        return cls()

    def open(self, method, url, is_async):
        self._method = method
        self._url = url
        FakeXHR.requests.append((method, url))

    def send(self):
        status, body = FakeXHR.responses.get(
            (self._method, self._url.split("?")[0]), (404, "")
        )
        self.status = status
        self.responseText = body


@pytest.fixture
def fake_pyodide(monkeypatch, tmp_path):
    """Pretend to be Pyodide with an instance folder and a dev server."""
    monkeypatch.setattr(website_files, "is_pyodide", lambda: True)
    instance = tmp_path / "instance"
    instance.mkdir()
    (instance / "vfs.css").write_text("")
    from drafter.client_server import commands

    monkeypatch.setattr(commands, "get_current_instance_root", lambda: str(instance))
    FakeXHR.responses = {}
    FakeXHR.requests = []
    js_module = MagicMock()
    js_module.XMLHttpRequest = FakeXHR
    monkeypatch.setitem(sys.modules, "js", js_module)
    return instance


class TestLookupPyodide:
    def test_found_in_virtual_filesystem(self, fake_pyodide):
        assert lookup_website_file("vfs.css").exists is True
        assert FakeXHR.requests == []

    def test_found_on_dev_server(self, fake_pyodide):
        FakeXHR.responses[("HEAD", "served.css")] = (200, "")
        assert lookup_website_file("served.css").exists is True

    def test_missing_uses_server_listing_for_suggestions(self, fake_pyodide):
        listing = json.dumps(
            {
                "entries": [
                    {"name": "styles.css", "is_dir": False},
                    {"name": "img", "is_dir": True},
                ]
            }
        )
        FakeXHR.responses[("GET", INTERNAL_ROUTES["LIST_FILES"])] = (200, listing)
        lookup = lookup_website_file("style.css")
        assert lookup.exists is False
        assert "styles.css" in lookup.siblings
        assert "img/" in lookup.siblings

    def test_unreachable_server_accepts_path(self, fake_pyodide, monkeypatch):
        # No HEAD answer other than an error status, and no listing route:
        # nothing can verify the file, so it is accepted rather than blocked.
        FakeXHR.responses[("HEAD", "mystery.css")] = (500, "")
        assert lookup_website_file("mystery.css").exists is None
        assert resolve_website_file("mystery.css", "add_website_css_file", "css") == (
            "mystery.css"
        )

    def test_listing_confirms_existence_when_head_is_inconclusive(self, fake_pyodide):
        FakeXHR.responses[("HEAD", "listed.css")] = (500, "")
        FakeXHR.responses[("GET", INTERNAL_ROUTES["LIST_FILES"])] = (
            200,
            json.dumps([{"name": "listed.css", "is_dir": False}]),
        )
        assert lookup_website_file("listed.css").exists is True

    def test_subfolder_listing_is_requested(self, fake_pyodide):
        FakeXHR.responses[("GET", INTERNAL_ROUTES["LIST_FILES"])] = (200, "[]")
        lookup_website_file("static/style.css")
        assert ("GET", f"{INTERNAL_ROUTES['LIST_FILES']}?path=static") in (
            FakeXHR.requests
        )


class TestLookupOtherWebRuntimes:
    def test_skulpt_cannot_check_and_accepts(self, monkeypatch):
        monkeypatch.setattr(website_files, "is_pyodide", lambda: False)
        monkeypatch.setattr(website_files, "is_web", lambda: True)
        assert lookup_website_file("anything.css").exists is None


# ============================================================================
# DEPLOY API
# ============================================================================


class TestAddWebsiteCssFile:
    def test_local_file_registers_link_and_file(self, program_dir, server):
        add_website_css_file("styles.css", server=server)
        assert server.get_config_setting("additional_css_files") == ["styles.css"]
        assert server.get_config_setting("additional_files") == ["styles.css"]

    def test_url_registers_link_only(self, program_dir, server):
        add_website_css_file("https://example.com/site.css", server=server)
        assert server.get_config_setting("additional_css_files") == [
            "https://example.com/site.css"
        ]
        assert server.get_config_setting("additional_files") == []

    def test_duplicates_are_ignored(self, program_dir, server):
        add_website_css_file("styles.css", server=server)
        add_website_css_file("styles.css", server=server)
        assert server.get_config_setting("additional_css_files") == ["styles.css"]
        assert server.get_config_setting("additional_files") == ["styles.css"]

    def test_missing_file_is_a_student_error(self, program_dir, server):
        with pytest.raises(StudentFacingError, match="file not found"):
            add_website_css_file("style.css", server=server)
        assert server.get_config_setting("additional_css_files") == []

    def test_uses_main_server_by_default(self, program_dir, monkeypatch):
        from drafter import deploy

        fake = ClientServer("main_for_css")
        monkeypatch.setattr(deploy, "get_main_server", lambda: fake)
        add_website_css_file("static/style.css")
        assert fake.get_config_setting("additional_css_files") == ["static/style.css"]


class TestAddWebsiteJs:
    def test_inline_js(self, server):
        add_website_js("console.log('hi');", server=server)
        assert server.get_config_setting("additional_js_content") == [
            "console.log('hi');"
        ]

    def test_js_file_local_and_url(self, program_dir, server):
        add_website_js_file("app.js", server=server)
        add_website_js_file("https://cdn.example.com/lib.js", server=server)
        assert server.get_config_setting("additional_js_files") == [
            "app.js",
            "https://cdn.example.com/lib.js",
        ]
        assert server.get_config_setting("additional_files") == ["app.js"]

    def test_js_file_missing_suggests(self, program_dir, server):
        with pytest.raises(StudentFacingError) as info:
            add_website_js_file("apps.js", server=server)
        assert "Did you mean 'app.js'?" in info.value.friendly_steps

    def test_filename_given_to_inline_helper(self, server):
        with pytest.raises(StudentFacingError) as info:
            add_website_js("app.js", server=server)
        assert info.value.friendly_title == "File Name Given Instead of JavaScript"
        assert any(
            "add_website_js_file('app.js')" in s for s in info.value.friendly_steps
        )


class TestAddWebsiteCssMistakes:
    def test_filename_given_to_add_website_css(self, server):
        with pytest.raises(StudentFacingError) as info:
            add_website_css("style.css", server=server)
        assert info.value.friendly_title == "File Name Given Instead of CSS"
        assert any(
            "add_website_css_file('style.css')" in s for s in info.value.friendly_steps
        )
        assert server.get_config_setting("additional_style_content") == []

    def test_url_given_to_add_website_css(self, server):
        with pytest.raises(StudentFacingError):
            add_website_css("https://example.com/site.css", server=server)

    def test_real_css_still_accepted(self, server):
        add_website_css("h1 { color: red; }", server=server)
        add_website_css("h1", "color: red;", server=server)
        # A selector that happens to end in ".css" with a body is fine too.
        add_website_css(".css", "color: red;", server=server)
        styles = server.get_config_setting("additional_style_content")
        assert styles[0] == "h1 { color: red; }"
        assert styles[1] == "h1 {color: red;}\n"
        assert styles[2] == ".css {color: red;}\n"

    def test_single_argument_with_spaces_is_css(self, server):
        # Not a file name: contains whitespace and no extension at the end.
        add_website_css("body{} .x{}", server=server)
        assert server.get_config_setting("additional_style_content") == ["body{} .x{}"]


class TestAddWebsiteFile:
    def test_registers_multiple_files(self, program_dir, server):
        add_website_file("words.txt", "Logo.PNG", "static/extra.js", server=server)
        assert server.get_config_setting("additional_files") == [
            "words.txt",
            "Logo.PNG",
            "static/extra.js",
        ]

    def test_no_arguments(self, server):
        with pytest.raises(StudentFacingError) as info:
            add_website_file(server=server)
        assert info.value.friendly_title == "No Website Files Given"

    def test_url_is_rejected(self, program_dir, server):
        with pytest.raises(StudentFacingError) as info:
            add_website_file("https://example.com/logo.png", server=server)
        assert "URL" in info.value.friendly_message

    def test_all_or_nothing(self, program_dir, server):
        """A bad name in the middle registers none of the files."""
        with pytest.raises(StudentFacingError):
            add_website_file("words.txt", "wordz.txt", server=server)
        assert server.get_config_setting("additional_files") == []

    def test_absolute_path_is_rejected(self, program_dir, server):
        with pytest.raises(StudentFacingError, match="absolute"):
            add_website_file(str(program_dir / "words.txt"), server=server)


# ============================================================================
# RENDERING
# ============================================================================


class TestSiteRendering:
    def make_site(self, **kwargs) -> Site:
        site = Site()
        site.set_configuration(ClientServerConfiguration(**kwargs))
        return site

    def test_css_files_are_linked_verbatim(self):
        site = self.make_site(
            additional_css_files=["styles.css", "https://example.com/a.css"]
        )
        data = site.render()
        urls = [link.url for link in data.additional_css]
        assert "styles.css" in urls
        assert "https://example.com/a.css" in urls
        # Nothing prefixed them with the internal assets route.
        assert not any(url.endswith("/styles.css") for url in urls)

    def test_css_files_come_after_theme_css(self):
        site = self.make_site(additional_css_files=["styles.css"])
        data = site.render()
        urls = [link.url for link in data.additional_css]
        assert urls[-1] == "styles.css"

    def test_js_files_become_scripts(self):
        site = self.make_site(
            additional_js_files=["app.js", "https://cdn.example.com/lib.js"],
            additional_js_content=["console.log(1)"],
        )
        data = site.render()
        assert data.additional_scripts == ["app.js", "https://cdn.example.com/lib.js"]
        assert data.additional_js == ["console.log(1)"]

    def test_remap_leaves_absolute_urls_alone(self):
        site = self.make_site(
            additional_css_content=["https://example.com/a.css", "b.css"]
        )
        remapped = site.remap_urls_to_assets(
            "https://example.com/a.css", "b.css", configuration=site.get_configuration()
        )
        assert remapped[0] == "https://example.com/a.css"
        assert remapped[1].endswith("/b.css") and remapped[1] != "b.css"


class FakeElement:
    def __init__(self, tag):
        self.tag = tag
        self.attributes = {}
        self.children = []

    def setAttribute(self, name, value):
        self.attributes[name] = value

    def appendChild(self, child):
        self.children.append(child)


class FakeDocument:
    def __init__(self):
        self.head = FakeElement("head")
        self.documentElement = FakeElement("html")

    def createElement(self, tag):
        return FakeElement(tag)


class TestAddScriptLink:
    def test_creates_script_with_src_in_head(self, monkeypatch):
        from drafter.bridge import dom

        document = FakeDocument()
        monkeypatch.setattr(dom, "get_document", lambda node: document)
        add_script_link(object(), "app.js", with_class="theme")
        assert len(document.head.children) == 1
        script = document.head.children[0]
        assert script.tag == "script"
        assert script.attributes == {"src": "app.js", "class": "theme"}


# ============================================================================
# BUILD
# ============================================================================


class TestCopyAdjacentFile:
    def test_copies_relative_file(self, program_dir, tmp_path, capsys):
        out = tmp_path / "dist"
        dest = copy_adjacent_file("styles.css", program_dir, out, label="website file")
        assert dest == out / "styles.css"
        assert dest.read_text() == "h1 { color: red; }"

    def test_copies_nested_file_keeping_folders(self, program_dir, tmp_path):
        out = tmp_path / "dist"
        dest = copy_adjacent_file("static/style.css", program_dir, out)
        assert dest == out / "static" / "style.css"
        assert dest.exists()

    @pytest.mark.parametrize(
        "reference", ["", "https://example.com/a.css", "//cdn/a.css", "data:text/css,"]
    )
    def test_skips_urls(self, program_dir, tmp_path, reference):
        assert copy_adjacent_file(reference, program_dir, tmp_path / "dist") is None

    def test_missing_file_warns(self, program_dir, tmp_path, capsys):
        assert copy_adjacent_file("gone.css", program_dir, tmp_path / "dist") is None
        assert "Warning: file not found: gone.css" in capsys.readouterr().out

    def test_copies_directory(self, program_dir, tmp_path):
        dest = copy_adjacent_file("static", program_dir, tmp_path / "dist")
        assert dest is not None
        assert (dest / "style.css").exists()

    def test_registered_files_flow_to_build_helper(self, program_dir, tmp_path, server):
        add_website_css_file("styles.css", server=server)
        add_website_file("words.txt", server=server)
        out = tmp_path / "dist"
        for name in server.get_config_setting("additional_files"):
            copy_adjacent_file(name, program_dir, out)
        assert (out / "styles.css").exists()
        assert (out / "words.txt").exists()
        assert pathlib.Path(out / "styles.css").read_text() == "h1 { color: red; }"


# ============================================================================
# BRIDGE: REPLAYED VS LIVE CONFIGURATION EVENTS
# ============================================================================


class TestBridgeContentUpdates:
    """UpdatedConfiguration events for the content lists must never be
    reported as unhandled: replayed startup events are no-ops (the initial
    render already included them) and later ones inject content live."""

    def make_bridge(self, **config_kwargs):
        from types import SimpleNamespace

        from drafter.bridge.client_bridge import ClientBridge

        renderer = MagicMock()
        renderer.get_scope.return_value = "scope"
        renderer.use_shadow_dom = False
        bridge = SimpleNamespace(
            configuration=ClientServerConfiguration(**config_kwargs),
            site_renderer=renderer,
            set_site_title=MagicMock(),
            _handle_debug_events=MagicMock(return_value=True),
            _applied_content=set(),
        )
        bridge._seed_applied_content = lambda: ClientBridge._seed_applied_content(
            bridge
        )
        bridge._apply_content_update = (
            lambda key, value: ClientBridge._apply_content_update(bridge, key, value)
        )
        return bridge

    def dispatch(self, bridge, key, value):
        from drafter.bridge.client_bridge import ClientBridge
        from drafter.data.details.config import UpdatedConfigurationEvent

        return ClientBridge.handle_server_event(
            bridge, UpdatedConfigurationEvent(key=key, value=value)
        )

    def test_site_title_event_is_handled(self):
        bridge = self.make_bridge()
        assert self.dispatch(bridge, "site_title", "Fortune Teller") is True
        bridge.set_site_title.assert_called_once_with("Fortune Teller")
        assert bridge.configuration.site_title == "Fortune Teller"

    def test_replayed_startup_events_are_no_ops(self, monkeypatch):
        from drafter.bridge import client_bridge

        bridge = self.make_bridge(
            additional_css_files=["styles.css"], additional_files=["styles.css"]
        )
        bridge._seed_applied_content()
        add_link = MagicMock()
        monkeypatch.setattr(client_bridge, "add_link", add_link)
        errors = MagicMock()
        monkeypatch.setattr(client_bridge, "report_bridge_error", errors)

        self.dispatch(bridge, "additional_css_files", "styles.css")
        self.dispatch(bridge, "additional_files", "styles.css")

        add_link.assert_not_called()
        errors.assert_not_called()
        assert bridge.configuration.additional_css_files == ["styles.css"]

    def test_live_updates_inject_into_the_page(self, monkeypatch):
        from drafter.bridge import client_bridge

        bridge = self.make_bridge()
        bridge._seed_applied_content()
        calls = {}
        for name in (
            "add_link",
            "add_style",
            "add_js",
            "add_script_link",
            "add_header",
        ):
            calls[name] = MagicMock()
            monkeypatch.setattr(client_bridge, name, calls[name])
        errors = MagicMock()
        monkeypatch.setattr(client_bridge, "report_bridge_error", errors)

        self.dispatch(bridge, "additional_css_files", "https://x/a.css")
        self.dispatch(bridge, "additional_style_content", "h1 {}")
        self.dispatch(bridge, "additional_js_content", "console.log(1)")
        self.dispatch(bridge, "additional_js_files", "app.js")
        self.dispatch(bridge, "additional_header_content", "<meta>")
        self.dispatch(bridge, "additional_files", "words.txt")

        calls["add_link"].assert_called_once()
        assert calls["add_link"].call_args.args[1] == "https://x/a.css"
        calls["add_style"].assert_called_once()
        calls["add_js"].assert_called_once()
        calls["add_script_link"].assert_called_once()
        calls["add_header"].assert_called_once()
        errors.assert_not_called()
        assert bridge.configuration.additional_files == ["words.txt"]
        # A second identical event does nothing more.
        self.dispatch(bridge, "additional_js_files", "app.js")
        calls["add_script_link"].assert_called_once()

    def test_relative_css_content_is_remapped_to_assets(self, monkeypatch):
        from drafter.bridge import client_bridge

        bridge = self.make_bridge()
        add_link = MagicMock()
        monkeypatch.setattr(client_bridge, "add_link", add_link)
        self.dispatch(bridge, "additional_css_content", "extra.css")
        assert add_link.call_args.args[1].endswith("/extra.css")
        assert add_link.call_args.args[1] != "extra.css"
