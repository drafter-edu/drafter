"""Guards the `drafter-docs build --api` reference against uncollectable modules.

`tools/gen_ref_pages.py` emits one mkdocstrings page per module under
`src/drafter`, and mkdocstrings aborts the whole build when griffe cannot
collect one of them. Griffe does not descend into a directory that lacks an
`__init__.py` (an implicit namespace package), even though Python imports
it happily, so such a directory breaks the API build without breaking any
other test.
"""

from pathlib import Path

import griffe

SRC = Path(__file__).parent.parent / "src"


def documented_module_names() -> list[str]:
    """Dotted names of the modules gen_ref_pages.py generates pages for."""
    names = []
    for path in sorted((SRC / "drafter").rglob("*.py")):
        parts = path.relative_to(SRC).with_suffix("").parts
        if parts[-1] == "__main__":
            continue
        if parts[-1] == "__init__":
            parts = parts[:-1]
        names.append(".".join(parts))
    return names


def test_every_module_is_collectable_for_the_api_reference():
    loader = griffe.GriffeLoader(search_paths=[str(SRC)])
    loader.load("drafter")

    names = documented_module_names()
    missing = []
    for name in names:
        try:
            loader.modules_collection[name]
        except KeyError:
            missing.append(name)

    assert names, "found no modules under src/drafter"
    assert not missing, (
        "griffe cannot collect these modules, so `drafter-docs build --api` "
        "would abort; check that every package directory on the way to them "
        f"has an __init__.py: {missing}"
    )
