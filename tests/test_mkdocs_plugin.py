"""Tests for the Drafter MkDocs code block plugin's page transformations."""

from pathlib import PurePosixPath
from types import SimpleNamespace
from unittest.mock import patch

import pytest

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
