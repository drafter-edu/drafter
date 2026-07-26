"""Docs coverage audit: every exported name has a primary reference page.

Implements CI gate 2 from STUDENT_DOCS_PLAN.md §11. Compares
`drafter.__all__` against the union of every docs page's `symbols`
front-matter, minus the reasoned exclusion list in
tools/docs_coverage_exclusions.yaml.

Usage:
    uv run python tools/docs_coverage.py            # report only (exit 0)
    uv run python tools/docs_coverage.py --strict   # fail on gaps (Phase E+)

The maintenance loop this enforces: adding a name to `drafter.__all__`
fails the strict gate until the name appears in some page's `symbols`
list or in the exclusion file with a reason.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
EXCLUSIONS = ROOT / "tools" / "docs_coverage_exclusions.yaml"

FRONT_MATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


def collect_documented_symbols() -> dict[str, list[str]]:
    """Map each symbol to the docs pages whose front-matter claims it.

    Returns:
        Mapping of symbol name to the list of docs-relative pages that
        list it in their `symbols` front-matter.
    """
    documented: dict[str, list[str]] = {}
    for path in DOCS.rglob("*.md"):
        match = FRONT_MATTER_RE.match(path.read_text(encoding="utf-8-sig"))
        if not match:
            continue
        try:
            meta = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            continue
        if not isinstance(meta, dict):
            continue
        for symbol in meta.get("symbols") or []:
            documented.setdefault(str(symbol), []).append(
                path.relative_to(DOCS).as_posix()
            )
    return documented


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero on undocumented or unknown symbols",
    )
    args = parser.parse_args()

    import drafter

    exported = set(drafter.__all__)
    with open(EXCLUSIONS, encoding="utf-8") as fd:
        exclusions: dict[str, str] = yaml.safe_load(fd) or {}

    documented = collect_documented_symbols()

    undocumented = sorted(exported - documented.keys() - exclusions.keys())
    unknown = sorted(documented.keys() - exported)
    stale_exclusions = sorted(set(exclusions) & documented.keys())
    covered = exported & documented.keys()

    print(
        f"docs coverage: {len(covered)}/{len(exported)} exported names documented, "
        f"{len(exclusions)} excluded with reasons."
    )
    problems = False
    if undocumented:
        problems = True
        print(
            f"\n{len(undocumented)} exported names with no primary page and no exclusion:"
        )
        for name in undocumented:
            print(f"  {name}")
    if unknown:
        problems = True
        print(f"\n{len(unknown)} symbols claimed by docs but not in drafter.__all__:")
        for name in unknown:
            print(f"  {name} ({', '.join(documented[name])})")
    if stale_exclusions:
        problems = True
        print(
            f"\n{len(stale_exclusions)} exclusions now documented (remove from exclusion list):"
        )
        for name in stale_exclusions:
            print(f"  {name}")

    if problems and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
