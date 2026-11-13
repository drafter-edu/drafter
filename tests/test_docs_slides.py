"""Contracts between the docs slide mode and the rest of the docs tooling.

Slide mode (`docs/assets/drafter-slides.js`) turns any documentation page into
a slide deck. Its layout behavior is exercised in a real browser by
`js/e2e/docs-slides.spec.ts`; this module covers the things that can drift
without any browser noticing:

- the site must actually load the slide-mode assets,
- the sections that slide mode leaves out must keep covering the four-link
  block the docs linter requires on Add to Your App pages, and must name
  headings the pages really use, and
- the opening sections that slide mode folds into the title slide must name
  headings the pages really use.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SLIDES_SCRIPT = DOCS / "assets" / "drafter-slides.js"
SLIDES_STYLES = DOCS / "assets" / "drafter-slides.css"


def _load_docs_lint() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "docs_lint", ROOT / "tools" / "docs_lint.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _section_list_in_script(name: str) -> list[str]:
    source = SLIDES_SCRIPT.read_text(encoding="utf-8")
    match = re.search(rf"var {name} = \[(.*?)\];", source, re.DOTALL)
    assert match is not None, f"{name} not found in drafter-slides.js"
    return re.findall(r'"([^"]+)"', match.group(1))


def _closing_sections_in_script() -> list[str]:
    return _section_list_in_script("CLOSING_SECTIONS")


def _opening_sections_in_script() -> list[str]:
    return _section_list_in_script("OPENING_SECTIONS")


def _section_headings_in_docs() -> set[str]:
    headings: set[str] = set()
    for page in DOCS.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        headings.update(re.findall(r"^## (.+?)\s*$", text, re.MULTILINE))
    return headings


def test_site_loads_the_slide_mode_assets() -> None:
    config = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))

    assert "assets/drafter-slides.js" in config["extra_javascript"]
    assert "assets/drafter-slides.css" in config["extra_css"]
    assert SLIDES_SCRIPT.is_file()
    assert SLIDES_STYLES.is_file()


def test_slide_mode_skips_the_whole_four_link_block() -> None:
    docs_lint = _load_docs_lint()
    skipped = _closing_sections_in_script()

    assert [name for name in docs_lint.FOUR_LINKS if name not in skipped] == []


def test_every_skipped_section_is_a_heading_the_docs_use() -> None:
    """A renamed or misspelled entry would silently stop being skipped."""
    headings = _section_headings_in_docs()

    unused = [name for name in _closing_sections_in_script() if name not in headings]
    assert unused == []


def test_slide_mode_skips_the_section_for_extra_depth() -> None:
    assert "In more depth" in _closing_sections_in_script()


def test_every_folded_opening_section_is_a_heading_the_docs_use() -> None:
    """A renamed or misspelled entry would silently become its own slide."""
    opening = _opening_sections_in_script()
    headings = _section_headings_in_docs()

    assert opening != []
    assert [name for name in opening if name not in headings] == []


def test_no_section_is_both_folded_and_skipped() -> None:
    skipped = _closing_sections_in_script()

    assert [name for name in _opening_sections_in_script() if name in skipped] == []


def test_sections_that_point_an_audience_onward_stay_in_the_deck() -> None:
    skipped = _closing_sections_in_script()

    assert "Next steps" not in skipped
    assert "Go deeper" not in skipped


def test_every_css_class_the_script_toggles_is_styled() -> None:
    """A renamed class would silently stop hiding or showing blocks."""
    script = SLIDES_SCRIPT.read_text(encoding="utf-8")
    styles = SLIDES_STYLES.read_text(encoding="utf-8")
    toggled = set(re.findall(r'var [A-Z_]+ = "(drafter-slides__[a-z-]+)";', script))

    assert toggled, "no class constants found in drafter-slides.js"
    missing = sorted(name for name in toggled if f".{name}" not in styles)
    assert missing == []
