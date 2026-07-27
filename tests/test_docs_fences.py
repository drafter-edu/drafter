"""Execute every runnable documentation fence under CPython (CI gate 1).

STUDENT_DOCS_PLAN.md §11: the exact copyable code in the docs is what gets
tested — no hidden setup. This harness extracts every ```python drafter
fence (and static ```python fences marked `test=true`) from docs/**/*.md
and, for each one:

- executes it with `start_server` stubbed to a no-op (routes are
  host-callable, so tests run without a browser);
- fails if the code raises before `start_server`;
- fails if any Drafter assertion prints a FAILURE line (assertions report
  rather than raise);
- for error-entry repros (fences marked `repro` on pages with `error_text`
  front-matter), expects the fence to raise an error containing the
  documented text instead.

Each fence runs against a throwaway main server so fences cannot interfere
with each other or with the rest of the test suite.
"""

from __future__ import annotations

import contextlib
import io
import re
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

import drafter
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import get_main_server, set_main_server

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

FRONT_MATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
FENCE_OPEN_RE = re.compile(r"^(\s*)```+\s*(.*)$")


@dataclass
class Fence:
    """One extracted runnable fence."""

    page: str
    lineno: int
    flags: set[str]
    code: str
    error_text: str | None

    @property
    def test_id(self) -> str:
        return f"{self.page}:{self.lineno}"

    @property
    def is_repro(self) -> bool:
        return "repro" in self.flags and self.error_text is not None


def parse_page(path: Path) -> list[Fence]:
    """Extract the runnable fences from one docs page.

    Args:
        path: The Markdown file to scan.

    Returns:
        The page's runnable fences (possibly empty).
    """
    text = path.read_text(encoding="utf-8-sig")
    error_text = None
    match = FRONT_MATTER_RE.match(text)
    if match:
        try:
            meta = yaml.safe_load(match.group(1))
            if isinstance(meta, dict):
                error_text = meta.get("error_text")
        except yaml.YAMLError:
            pass

    fences: list[Fence] = []
    lines = text.splitlines()
    fence_ticks = 0  # backtick count of the open fence; 0 = not in a fence
    collecting = False
    fence_flags: set[str] = set()
    fence_start = 0
    fence_lines: list[str] = []
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not fence_ticks:
            if not stripped.startswith("```"):
                continue
            info = stripped.lstrip("`").strip()
            if not info:
                continue
            fence_ticks = len(stripped) - len(stripped.lstrip("`"))
            tokens = info.split()
            collecting = tokens[0] == "python"
            fence_flags = set(tokens[1:])
            fence_start = lineno
            fence_lines = []
            continue
        # Only a bare fence of at least the opening length closes it; shorter
        # fences inside (e.g. ``` within ````markdown) are fence content.
        if stripped.startswith("```"):
            ticks = len(stripped) - len(stripped.lstrip("`"))
            if ticks >= fence_ticks and not stripped.lstrip("`").strip():
                fence_ticks = 0
                runnable = "drafter" in fence_flags or "test=true" in fence_flags
                if collecting and runnable:
                    fences.append(
                        Fence(
                            page=path.relative_to(DOCS).as_posix(),
                            lineno=fence_start,
                            flags=fence_flags,
                            code="\n".join(fence_lines),
                            error_text=error_text,
                        )
                    )
                continue
        fence_lines.append(line)
    return fences


def discover_fences() -> list[Fence]:
    """Collect every runnable fence across the docs tree."""
    fences: list[Fence] = []
    for path in sorted(DOCS.rglob("*.md")):
        if "drafter-demos" in path.parts:
            continue
        fences.extend(parse_page(path))
    return fences


ALL_FENCES = discover_fences()


@contextlib.contextmanager
def sandboxed_drafter(monkeypatch, name: str):
    """Give a fence its own main server and a stubbed start_server."""
    monkeypatch.setattr(drafter, "start_server", lambda *args, **kwargs: None)
    previous = get_main_server()
    set_main_server(ClientServer(name))
    try:
        yield
    finally:
        set_main_server(previous)


def test_fence_discovery_runs():
    """The extractor itself must work even while the docs are all stubs."""
    assert isinstance(ALL_FENCES, list)


@pytest.mark.parametrize("fence", ALL_FENCES, ids=lambda fence: fence.test_id)
def test_docs_fence(fence: Fence, monkeypatch):
    compiled = compile(fence.code, f"docs/{fence.page}", "exec")
    output = io.StringIO()
    with sandboxed_drafter(monkeypatch, f"DOCS_FENCE_{fence.lineno}"):
        if fence.is_repro:
            with pytest.raises(Exception) as excinfo:
                with contextlib.redirect_stdout(output):
                    exec(compiled, {"__name__": "__main__"})
            assert fence.error_text in str(excinfo.value), (
                f"Repro fence raised, but the error did not contain the "
                f"documented error_text.\nDocumented: {fence.error_text}\n"
                f"Raised: {excinfo.value}"
            )
            return
        with contextlib.redirect_stdout(output):
            exec(compiled, {"__name__": "__main__"})
    failures = [
        line for line in output.getvalue().splitlines() if line.startswith("FAILURE")
    ]
    assert not failures, "Drafter assertions failed:\n" + "\n".join(failures)
