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
