"""Rename docs/ files and folders to a consistent naming convention.

Convention: all lowercase, one (at most two) words, underscores as the
separator when two words are needed.

Edit the RENAMES table below to refine any choices, then run from the
repo root:

    python tools/rename_docs.py --dry-run   # print the plan, touch nothing
    python tools/rename_docs.py             # perform the renames (uses git mv)

Each entry is (path relative to docs/, new basename). Only the last path
segment changes per entry; renames are applied deepest-first so parent
folder renames never invalidate child paths. Remove a line to skip that
rename.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"

RENAMES = [
    # --- files ---------------------------------------------------------
    ("ComponentDocs/AdvancedComponents/filemanagement/fileupload.md", "file_upload.md"),
    ("ComponentDocs/AdvancedComponents/formatting/divrow.md", "div_row.md"),
    ("ComponentDocs/AdvancedComponents/formatting/linebreak.md", "line_break.md"),
    ("ComponentDocs/AdvancedComponents/formatting/preformattedtext.md", "preformatted_text.md"),
    ("ComponentDocs/BasicComponents/bulletedlist.md", "bulleted_list.md"),
    ("ComponentDocs/BasicComponents/numberedlist.md", "numbered_list.md"),
    ("ComponentDocs/StylingComponents/addingwebsitecss.md", "website_css.md"),
    ("ComponentDocs/StylingComponents/cssclasses.md", "css_classes.md"),
    ("ComponentDocs/StylingComponents/cssstyletags.md", "style_tags.md"),
    ("ComponentDocs/StylingComponents/keywordparameters.md", "keyword_parameters.md"),
    ("ComponentDocs/StylingComponents/stylingfunctions.md", "styling_functions.md"),
    # Empty file that was missing an extension entirely:
    ("ComponentDocs/StartIntro", "start_intro.md"),
    # --- folders -------------------------------------------------------
    ("ComponentDocs/AdvancedComponents/filemanagement", "file_management"),
    ("ComponentDocs/Styling/Css", "css"),
    ("ComponentDocs/Styling/components/postion", "position"),  # also fixes typo
    ("ComponentDocs/Styling/components/text/fonttype", "font_type"),
    ("ComponentDocs/AdvancedComponents", "advanced"),
    ("ComponentDocs/BasicComponents", "basic"),
    ("ComponentDocs/SpecializedComponents", "specialized"),
    ("ComponentDocs/Styling", "styling"),
    ("ComponentDocs/StylingComponents", "styling_components"),
    ("ComponentDocs", "components"),
    ("Curious", "curious"),
    ("quick start new", "quickstart_new"),
]


def git_mv(old: Path, new: Path) -> None:
    """git mv, with a two-step dance for case-only renames (Windows)."""
    case_only = str(old).lower() == str(new).lower()
    if case_only:
        tmp = old.with_name(old.name + "__rename_tmp")
        subprocess.run(["git", "mv", str(old), str(tmp)], cwd=REPO_ROOT, check=True)
        subprocess.run(["git", "mv", str(tmp), str(new)], cwd=REPO_ROOT, check=True)
    else:
        subprocess.run(["git", "mv", str(old), str(new)], cwd=REPO_ROOT, check=True)


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    # Deepest paths first, so folder renames happen after their contents.
    planned = sorted(RENAMES, key=lambda r: len(Path(r[0]).parts), reverse=True)

    # Sanity-check the plan before touching anything.
    errors = []
    seen_targets = set()
    for rel, new_name in planned:
        old = DOCS / rel
        new = old.with_name(new_name)
        if not old.exists():
            errors.append(f"missing:   {old.relative_to(REPO_ROOT)}")
        if new.exists() and str(old).lower() != str(new).lower():
            errors.append(f"collision: {new.relative_to(REPO_ROOT)} already exists")
        target = str(new).lower()
        if target in seen_targets:
            errors.append(f"duplicate target: {new.relative_to(REPO_ROOT)}")
        seen_targets.add(target)
    if errors:
        print("Refusing to run — fix these first:")
        for e in errors:
            print(f"  {e}")
        return 1

    width = max(len(str((DOCS / rel).relative_to(REPO_ROOT))) for rel, _ in planned)
    for rel, new_name in planned:
        old = DOCS / rel
        new = old.with_name(new_name)
        print(f"{str(old.relative_to(REPO_ROOT)):<{width}}  ->  {new.relative_to(REPO_ROOT)}")
        if not dry_run:
            git_mv(old, new)

    # Report any files still missing an extension.
    missing_ext = [p for p in DOCS.rglob("*") if p.is_file() and "." not in p.name]
    if missing_ext:
        print("\nFiles still missing an extension:")
        for p in missing_ext:
            print(f"  {p.relative_to(REPO_ROOT)}")

    if dry_run:
        print("\n(dry run — nothing was renamed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
