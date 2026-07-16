"""Wrapper around MkDocs CLI that adds an optional --dev flag.

When --dev is provided, Drafter's MkDocs plugin compiles embedded demos with
`pyodide_package_style=build` by exporting DRAFTER_MKDOCS_DEV=1 for the mkdocs
process.
"""

from __future__ import annotations

import os
import subprocess
import sys


def _strip_dev_flag(argv: list[str]) -> tuple[list[str], bool]:
    filtered: list[str] = []
    dev_mode = False
    for arg in argv:
        if arg == "--dev":
            dev_mode = True
            continue
        filtered.append(arg)
    return filtered, dev_mode


def main() -> int:
    forwarded_args, dev_mode = _strip_dev_flag(sys.argv[1:])
    env = os.environ.copy()
    if dev_mode:
        env["DRAFTER_MKDOCS_DEV"] = "1"

    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", *forwarded_args],
        env=env,
        check=False,
    )
    return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
