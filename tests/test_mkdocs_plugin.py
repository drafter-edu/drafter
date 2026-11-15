"""Tests for the Drafter MkDocs code block plugin's page transformations."""

from pathlib import PurePosixPath
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from drafter.configuration import get_parser
from drafter.docs.mkdocs_plugin import DrafterCodeBlockPlugin

MARKDOWN = """# Example

```python drafter
from drafter import *

start_server()
```
"""


def make_plugin(**overrides) -> DrafterCodeBlockPlugin:
    plugin = DrafterCodeBlockPlugin()
    errors, warnings = plugin.load_config(overrides)
    assert not errors and not warnings
    return plugin


def make_page(src_uri="examples/demo.md", url="examples/demo/"):
    return SimpleNamespace(file=SimpleNamespace(src_uri=src_uri), url=url)


def run_page_markdown(plugin, page, markdown=MARKDOWN):
    with patch.object(
        plugin,
        "_build_demo",
        return_value=PurePosixPath("drafter-demos/demo-1-abc/index.html"),
    ):
        return plugin.on_page_markdown(markdown, page=page, config={}, files=None)


def test_marked_fence_becomes_source_and_iframe():
    plugin = make_plugin()
    page = make_page()
    result = run_page_markdown(plugin, page)
    assert "```python\nfrom drafter import *" in result
    assert '<div class="drafter-demo" data-drafter-demo="' in result
    assert "<iframe" in result
    assert page.file.src_uri in plugin._pages_with_demos


def test_demo_frame_may_show_alert_and_prompt_boxes():
    # A demo's `js` is its own frame, so `js.alert(...)` in a demo is shown
    # by the frame, which a sandbox forbids unless it allows modals.
    result = run_page_markdown(make_plugin(), make_page())

    sandbox = result.split('sandbox="')[1].split('"')[0].split()
    assert "allow-modals" in sandbox
    assert {"allow-scripts", "allow-forms", "allow-same-origin"} <= set(sandbox)


def capture_compile_command(plugin, tmp_path) -> list[str]:
    """Run `_build_demo` with the compile subprocess replaced by a recorder."""
    plugin._site_output_dir = tmp_path / "site"
    plugin._temp_root = tmp_path / "temp"
    plugin._docs_dir = tmp_path / "docs"
    plugin._temp_root.mkdir()
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        (plugin._site_output_dir / "demo-1").mkdir(parents=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with patch("drafter.docs.mkdocs_plugin.subprocess.run", fake_run):
        plugin._build_demo("from drafter import *\n", "demo-1")
    return commands[0]


@pytest.mark.parametrize("overrides", [{}, {"shared_runtime": True}])
def test_compile_command_uses_only_flags_the_cli_knows(tmp_path, overrides):
    # The command once passed `--console_mode`; the real flag is
    # `--console-mode`, and the CLI ignores flags it does not know, so the
    # demos silently ran without the console setting.
    command = capture_compile_command(make_plugin(**overrides), tmp_path)

    parser = get_parser("compile_site")
    arguments = [argument for argument in command[3:] if argument]
    parsed, unknown = parser.parse_known_args(arguments)

    assert unknown == []
    assert parsed.console_mode == "hover"


def test_unmarked_fence_left_alone():
    plugin = make_plugin()
    page = make_page()
    markdown = "```python\nprint('hi')\n```\n"
    result = run_page_markdown(plugin, page, markdown)
    assert result == markdown
    assert not plugin._pages_with_demos


def test_page_content_injects_host_and_editor():
    plugin = make_plugin()
    page = make_page()
    run_page_markdown(plugin, page)
    html = plugin.on_page_content("<p>body</p>", page=page, config={}, files=None)
    assert "drafter.pyodide.js" in html
    assert "drafter-edit-button" in html
    assert ".drafter-edit-area" in html
    assert html.endswith("<p>body</p>")


@pytest.mark.parametrize(
    "overrides",
    [{"editable": False}, {"show_source": False}],
)
def test_editor_not_injected_when_disabled(overrides):
    plugin = make_plugin(**overrides)
    page = make_page()
    run_page_markdown(plugin, page)
    html = plugin.on_page_content("<p>body</p>", page=page, config={}, files=None)
    assert "drafter.pyodide.js" in html
    assert "drafter-edit-button" not in html


def test_no_injection_without_demos():
    plugin = make_plugin()
    page = make_page()
    html = plugin.on_page_content("<p>body</p>", page=page, config={}, files=None)
    assert html == "<p>body</p>"


def test_hl_lines_param_passes_through_to_source_fence():
    plugin = make_plugin()
    page = make_page()
    markdown = '```python drafter hl_lines="2-4 7"\ncode\n```\n'
    result = run_page_markdown(plugin, page, markdown)
    assert '```python hl_lines="2-4 7"\ncode\n```' in result
    assert "<iframe" in result


def test_hl_lines_accepts_commas_and_bare_values():
    plugin = make_plugin()
    page = make_page()
    markdown = "```python drafter hl_lines=2,4-6\ncode\n```\n"
    result = run_page_markdown(plugin, page, markdown)
    assert '```python hl_lines="2 4-6"\ncode\n```' in result


def test_height_param_sets_demo_iframe_height():
    plugin = make_plugin(iframe_height=430)
    page = make_page()
    markdown = "```python drafter height=300\ncode\n```\n"
    result = run_page_markdown(plugin, page, markdown)
    assert "min-height: 300px" in result
    assert "min-height: 430px" not in result
    assert "```python\ncode\n```" in result
    assert "height=300" not in result
    assert "<iframe" in result


def test_height_param_accepts_css_lengths():
    plugin = make_plugin()
    page = make_page()
    markdown = "```python drafter height=20em\ncode\n```\n"
    result = run_page_markdown(plugin, page, markdown)
    assert "min-height: 20em" in result


def test_iframe_height_config_used_without_height_param():
    plugin = make_plugin(iframe_height=430)
    page = make_page()
    result = run_page_markdown(plugin, page)
    assert "min-height: 430px" in result


def test_invalid_params_fall_back_to_defaults():
    plugin = make_plugin(iframe_height=430)
    page = make_page()
    markdown = "```python drafter hl_lines=abc height=tall\ncode\n```\n"
    result = run_page_markdown(plugin, page, markdown)
    assert "hl_lines" not in result
    assert "min-height: 430px" in result
    assert "```python\ncode\n```" in result
    assert "<iframe" in result


def test_params_on_plain_fence_apply_without_demo():
    plugin = make_plugin()
    page = make_page()
    markdown = '```python hl_lines="2" height=150\nprint("hi")\n```\n'
    result = run_page_markdown(plugin, page, markdown)
    assert "<iframe" not in result
    assert not plugin._pages_with_demos
    # height only applies to demos; it is stripped from plain fences.
    assert "height" not in result.replace("hl_lines", "")
    assert '```python hl_lines="2"\nprint("hi")\n```' in result


def test_source_collapsed_wraps_source_in_closed_details_block():
    plugin = make_plugin()
    page = make_page()
    markdown = '```python drafter source=collapsed hl_lines="2"\nline1\n\nline3\n```\n'
    result = run_page_markdown(plugin, page, markdown)
    expected = (
        '??? note "Show the code"\n'
        "\n"
        '    ```python hl_lines="2"\n'
        "    line1\n"
        "\n"
        "    line3\n"
        "    ```\n"
        "\n"
        '<div class="drafter-demo"'
    )
    assert expected in result
    assert "source=" not in result
    assert "<iframe" in result


def test_source_hidden_omits_source_block():
    plugin = make_plugin()
    page = make_page()
    markdown = "```python drafter source=hidden\ncode\n```\n"
    result = run_page_markdown(plugin, page, markdown)
    assert "```" not in result
    assert "code" not in result.replace("data-drafter-demo", "")
    assert "<iframe" in result
    assert page.file.src_uri in plugin._pages_with_demos


def test_source_shown_is_default_and_case_insensitive():
    plugin = make_plugin()
    page = make_page()
    markdown = "```python drafter source=SHOWN\ncode\n```\n"
    result = run_page_markdown(plugin, page, markdown)
    assert "```python\ncode\n```\n\n<div" in result
    assert "???" not in result


def test_invalid_source_value_falls_back_to_shown():
    plugin = make_plugin()
    page = make_page()
    markdown = "```python drafter source=sometimes\ncode\n```\n"
    result = run_page_markdown(plugin, page, markdown)
    assert "```python\ncode\n```" in result
    assert "???" not in result
    assert "source" not in result
    assert "<iframe" in result


def test_source_param_stripped_from_plain_fence():
    plugin = make_plugin()
    page = make_page()
    markdown = "```python source=hidden\nprint('hi')\n```\n"
    result = run_page_markdown(plugin, page, markdown)
    assert result == "```python\nprint('hi')\n```\n"
    assert not plugin._pages_with_demos


def test_plain_fence_without_params_untouched():
    plugin = make_plugin()
    page = make_page()
    markdown = '```text some info\ntitle="x"\n```\n'
    result = run_page_markdown(plugin, page, markdown)
    assert result == markdown


def test_unknown_params_preserved_on_source_fence():
    plugin = make_plugin()
    page = make_page()
    markdown = '```python drafter title="Example" height=100\ncode\n```\n'
    result = run_page_markdown(plugin, page, markdown)
    assert '```python title="Example"\ncode\n```' in result
    assert "min-height: 100px" in result
