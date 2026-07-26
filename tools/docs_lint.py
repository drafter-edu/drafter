"""Documentation linter: URL contract, front-matter schema, template sections.

Implements CI gate 3 (template completeness) and parts of gate 4 (structure)
from STUDENT_DOCS_PLAN.md §11:

- every page in tools/docs_manifest.yaml exists, and every Markdown page in
  docs/ is either in the manifest or explicitly allowed;
- front-matter parses and carries the required keys with valid values;
- pages that are no longer stubs (`status: stub` removed) contain the
  headings their template requires (§7), the four-link block on Add to Your
  App pages, and `error_text` front-matter on error entries;
- every image has alt text and every fence has a language tag;
- Teach/Developer pages are excluded from the student search index.

Usage:
    uv run python tools/docs_lint.py

Exit code is nonzero when any check fails; the report lists each page with
what is missing, so incomplete pages are a CI artifact rather than a manual
sweep.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "docs_manifest.yaml"
DOCS = ROOT / "docs"

PAGE_TYPES = {
    "tutorial",
    "concept",
    "how-to",
    "component",
    "api",
    "example",
    "error",
    "gallery",
    "lesson",
    "misconception",
    "archetype",
    "index",
    "reference",
    "troubleshooting",
    "playground",
}
AUDIENCES = {"S", "T", "D"}
PRIORITIES = {"P0", "P1", "P2"}
LEVELS = {"L1", "L2", "L3", "L4"}

#: Headings required on finished (non-stub) pages, by page_type (§7).
#: Matched case-insensitively as substrings of any heading line.
REQUIRED_HEADINGS: dict[str, list[str]] = {
    "tutorial": [
        "What you'll build",
        "What you need",
        "Common problems",
        "Name it",
        "Make it yours",
        "Next steps",
    ],
    "concept": [
        "In one sentence",
        "The idea",
        "See it",
        "What this means for your code",
        "Where people get confused",
        "Go deeper",
    ],
    "how-to": [
        "Goal",
        "Before you start",
        "Common problems",
    ],
    "component": [
        "Description",
        "Syntax",
        "Parameters",
        "Examples",
        "Notes",
        "Related components",
    ],
    "example": [
        "What it does",
        "Try it",
        "The code",
        "How it works",
        "Make it yours",
        "Tests",
        "Likely errors",
        "Related",
    ],
    "error": [
        "The error",
        "What it means",
        "Where to look",
        "Check",
        "Fix",
        "Confirm",
        "Prevent",
        "Understand",
    ],
    "gallery": [
        "Try it",
        "Concepts used",
        "Tour of the code",
        "State and routes",
        "Remix it",
    ],
    "lesson": [
        "Session goal",
        "Audience and timing",
        "Prerequisites",
        "Materials",
        "Plan",
        "Checks for understanding",
        "Common stumbles",
        "Extensions",
        "Assessment ideas",
    ],
}

#: The four-link block required on every finished Add to Your App page (§6.3).
FOUR_LINKS = ["Understand it", "See another example", "Look it up", "Fix a problem"]

#: Guided projects must show the finished app before any code (§7.1).
GUIDED_PROJECT_HEADING = "Try the finished app"

FRONT_MATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
EMPTY_ALT_IMAGE_RE = re.compile(r"!\[\s*\]\(")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)


def split_page(text: str) -> tuple[dict | None, str]:
    """Split a page into parsed front-matter and body.

    Args:
        text: The raw page source.

    Returns:
        A (front_matter, body) pair; front_matter is None when absent or
        unparseable.
    """
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return None, text
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None, text[match.end() :]
    if not isinstance(meta, dict):
        return None, text[match.end() :]
    return meta, text[match.end() :]


def check_fences(body: str) -> list[str]:
    """Find fence-opening lines that lack a language tag.

    Args:
        body: The page body.

    Returns:
        Problem descriptions, one per untagged fence.
    """
    problems = []
    fence_ticks = 0  # backtick count of the open fence; 0 = not in a fence
    for lineno, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("```"):
            continue
        ticks = len(stripped) - len(stripped.lstrip("`"))
        info = stripped.lstrip("`").strip()
        if fence_ticks:
            # Only a bare fence of at least the opening length closes it;
            # shorter fences inside (e.g. ``` within ````markdown) are content.
            if ticks >= fence_ticks and not info:
                fence_ticks = 0
            continue
        fence_ticks = ticks
        if not info:
            problems.append(f"line {lineno}: code fence without a language tag")
    return problems


def check_page(rel_path: str, meta: dict | None, body: str) -> list[str]:
    """Run all per-page checks.

    Args:
        rel_path: Docs-relative path with forward slashes.
        meta: Parsed front-matter, or None.
        body: The page body.

    Returns:
        A list of problem descriptions (empty when the page is clean).
    """
    problems = []
    if meta is None:
        return ["missing or unparseable front-matter"]

    for key in ("page_type", "title", "audience", "priority", "outcome"):
        if key not in meta:
            problems.append(f"front-matter missing `{key}`")
    for key in ("prereqs", "symbols"):
        if not isinstance(meta.get(key), list):
            problems.append(f"front-matter `{key}` must be a list")
    if meta.get("page_type") not in PAGE_TYPES:
        problems.append(f"invalid page_type: {meta.get('page_type')!r}")
    if meta.get("audience") not in AUDIENCES:
        problems.append(f"invalid audience: {meta.get('audience')!r}")
    if meta.get("priority") not in PRIORITIES:
        problems.append(f"invalid priority: {meta.get('priority')!r}")
    if "level" in meta and meta["level"] not in LEVELS:
        problems.append(f"invalid level: {meta.get('level')!r}")
    if meta.get("audience") in ("T", "D"):
        if not (isinstance(meta.get("search"), dict) and meta["search"].get("exclude")):
            problems.append("Teach/Dev page must set `search: {exclude: true}`")

    if EMPTY_ALT_IMAGE_RE.search(body):
        problems.append("image with empty alt text")
    problems.extend(check_fences(body))

    if meta.get("status") == "stub":
        return problems  # Stubs are exempt from content-completeness checks.

    page_type = meta.get("page_type")
    headings = [h.strip().lower() for h in HEADING_RE.findall(body)]

    def has_heading(required: str) -> bool:
        needle = required.lower()
        return any(needle in heading for heading in headings)

    for required in REQUIRED_HEADINGS.get(page_type, []):
        if not has_heading(required):
            problems.append(f"missing required section: {required}")

    if page_type == "tutorial" and rel_path.startswith("tutorials/"):
        if not has_heading(GUIDED_PROJECT_HEADING):
            problems.append(f"missing required section: {GUIDED_PROJECT_HEADING}")

    if rel_path.startswith("add/") and page_type == "how-to":
        for link_label in FOUR_LINKS:
            if link_label.lower() not in body.lower():
                problems.append(f"missing four-link block entry: {link_label}")

    if page_type == "error" and not meta.get("error_text"):
        problems.append("error entry missing `error_text` front-matter")

    return problems


def main() -> int:
    with open(MANIFEST, encoding="utf-8") as fd:
        manifest_paths = {page["path"] for page in yaml.safe_load(fd)["pages"]}

    failures: dict[str, list[str]] = {}

    on_disk = {
        path.relative_to(DOCS).as_posix()
        for path in DOCS.rglob("*.md")
        if "drafter-demos" not in path.parts
    }
    for missing in sorted(manifest_paths - on_disk):
        failures.setdefault(missing, []).append("in manifest but missing from docs/")
    for extra in sorted(on_disk - manifest_paths):
        failures.setdefault(extra, []).append(
            "not in tools/docs_manifest.yaml (add it there first: the manifest "
            "is the URL contract)"
        )

    for rel_path in sorted(on_disk & manifest_paths):
        text = (DOCS / rel_path).read_text(encoding="utf-8-sig")
        meta, body = split_page(text)
        problems = check_page(rel_path, meta, body)
        if problems:
            failures[rel_path] = failures.get(rel_path, []) + problems

    if failures:
        print(f"docs lint: {len(failures)} pages with problems\n")
        for rel_path in sorted(failures):
            print(rel_path)
            for problem in failures[rel_path]:
                print(f"  - {problem}")
        return 1
    print(f"docs lint: {len(on_disk)} pages clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
