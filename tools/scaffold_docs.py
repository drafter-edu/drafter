"""Scaffold and verify the documentation tree from tools/docs_manifest.yaml.

The manifest is the URL contract from STUDENT_DOCS_PLAN.md §5: one entry per
planned page with its final front-matter seed. This script materializes that
contract:

    uv run python tools/scaffold_docs.py            # create missing stubs
    uv run python tools/scaffold_docs.py --check    # verify, do not write

Stubs are created with `status: stub` in their front-matter. Authors replace
the stub body and delete that line when they write the page; the docs linter
only enforces per-template required sections on pages that are no longer
stubs. Existing files are never overwritten.

Teach and Developer pages are excluded from the student search index
(mkdocs-material's `search: exclude` front-matter), per the Phase A decision
log (Q15).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "docs_manifest.yaml"
DOCS = ROOT / "docs"

#: Audiences whose pages stay out of the default student search index.
SEARCH_EXCLUDED_AUDIENCES = {"T", "D"}


def load_manifest() -> list[dict]:
    """Read the manifest and return its page entries.

    Returns:
        The list of page dictionaries from the manifest.
    """
    with open(MANIFEST, encoding="utf-8") as fd:
        data = yaml.safe_load(fd)
    return data["pages"]


def front_matter(page: dict) -> str:
    """Build the YAML front-matter block for a stub page.

    Args:
        page: One manifest entry.

    Returns:
        The front-matter string, including the closing delimiter.
    """
    # The front-matter key is page_type, not template: MkDocs reserves the
    # `template` meta key for overriding the page's Jinja template.
    lines = ["---"]
    lines.append(f"page_type: {page['template']}")
    lines.append(yaml.safe_dump({"title": page["title"]}, allow_unicode=True).strip())
    if page.get("level"):
        lines.append(f"level: {page['level']}")
    lines.append(f"audience: {page['audience']}")
    lines.append(f"priority: {page['priority']}")
    lines.append("prereqs: []")
    symbols = page.get("symbols", [])
    if symbols:
        lines.append("symbols:")
        lines.extend(f"  - {symbol}" for symbol in symbols)
    else:
        lines.append("symbols: []")
    lines.append(
        yaml.safe_dump({"outcome": page["outcome"]}, allow_unicode=True).strip()
    )
    if page["audience"] in SEARCH_EXCLUDED_AUDIENCES:
        lines.append("search:")
        lines.append("  exclude: true")
    lines.append("status: stub")
    lines.append("---")
    return "\n".join(lines)


def stub_body(page: dict) -> str:
    """Build the placeholder body for a stub page.

    Args:
        page: One manifest entry.

    Returns:
        The Markdown body for the stub.
    """
    return (
        f"# {page['title']}\n"
        "\n"
        '!!! note "Planned page"\n'
        f"    This page is planned ({page['priority']}) but not yet written.\n"
        f"    When finished, it will help you: {page['outcome'].rstrip('.').lower()}.\n"
    )


def scaffold(check_only: bool) -> int:
    """Create missing stub pages, or verify the tree in check mode.

    Args:
        check_only: When True, report missing pages without writing.

    Returns:
        Process exit code (0 on success, 1 when --check finds problems).
    """
    pages = load_manifest()
    seen: set[str] = set()
    duplicates = [p["path"] for p in pages if p["path"] in seen or seen.add(p["path"])]
    if duplicates:
        print(f"Manifest contains duplicate paths: {duplicates}")
        return 1

    created, missing = [], []
    for page in pages:
        target = DOCS / page["path"]
        if target.exists():
            continue
        if check_only:
            missing.append(page["path"])
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            front_matter(page) + "\n\n" + stub_body(page),
            encoding="utf-8",
            newline="\n",
        )
        created.append(page["path"])

    if check_only:
        if missing:
            print(f"{len(missing)} manifest pages missing from docs/:")
            for path in missing:
                print(f"  {path}")
            return 1
        print(f"All {len(pages)} manifest pages present.")
        return 0

    print(
        f"Created {len(created)} stub pages ({len(pages) - len(created)} already existed)."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify every manifest page exists; write nothing",
    )
    args = parser.parse_args()
    return scaffold(check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
