"""Generate the API reference pages for mkdocstrings.

Executed by the mkdocs-gen-files plugin during `mkdocs build` (see
mkdocs.yml). Creates one virtual page per module under reference/api/,
each containing a mkdocstrings identifier block, plus the SUMMARY.md
navigation file consumed by mkdocs-literate-nav.

Rendering every module through mkdocstrings dominates build time, so the
full reference is only generated when DRAFTER_MKDOCS_API is set (the
`drafter-docs --api` flag). Otherwise a single placeholder page is
emitted so the nav entry in mkdocs.yml still resolves.
"""

import os
from pathlib import Path

from tqdm import tqdm
import mkdocs_gen_files

if os.getenv("DRAFTER_MKDOCS_API", "").strip().lower() not in {
    "1",
    "true",
    "yes",
    "on",
}:
    with mkdocs_gen_files.open("reference/api/index.md", "w") as fd:
        fd.write(
            "# API Reference\n\n"
            "The full API reference was skipped to speed up this build.\n\n"
            "Rebuild with `uv run drafter-docs build --api` (or serve with "
            "`uv run drafter-docs serve --api`) to include it.\n"
        )
    with mkdocs_gen_files.open("reference/api/SUMMARY.md", "w") as nav_file:
        nav_file.write("* [Overview](index.md)\n")
    print("Skipping full API reference (pass --api to drafter-docs to build it).")
    raise SystemExit(0)

nav = mkdocs_gen_files.Nav()

root = Path(__file__).parent.parent
src = root / "src"

for path in tqdm(sorted(src.rglob("*.py")), desc="Generating API reference pages"):
    module_path = path.relative_to(src).with_suffix("")
    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("reference/api", doc_path)

    parts = tuple(module_path.parts)

    # The typings package holds Pyodide/js interface stubs, not real API.
    if "typings" in parts:
        continue
    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue
    elif parts[-1] == "index":
        # A module literally named index.py (router/defaults/index.py) would
        # collide with its package's __init__ page (index.md), putting the
        # same Page in the nav twice — which sends section-index's on_nav
        # into an infinite loop. Give it a distinct filename.
        doc_path = doc_path.with_name("index_.md")
        full_doc_path = full_doc_path.with_name("index_.md")
    if not parts:
        continue

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        fd.write(f"::: {'.'.join(parts)}\n")

    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(root))

with mkdocs_gen_files.open("reference/api/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())

print("API reference pages generated successfully.")
