"""Shared on-disk debug log for errors reported by running Drafter sites.

While a site is not in production mode, the browser posts error reports
(canonical ErrorDetails envelopes plus the same environment details the
bug-report bundle records) to the local development server, which appends
them here. The log lives next to the student's main file and is shared by
every Drafter site running from the same folder.

Format: JSON Lines (one JSON object per line). Each line is written with a
single append, so several dev servers writing to the same file can at worst
interleave within one line; readers should simply skip lines that fail to
parse. When the file grows past ``MAX_LOG_BYTES`` it is trimmed down to
roughly ``TRIM_TARGET_BYTES`` by dropping the oldest lines.

Writing is strictly best-effort: a failure to append prints one message to
the CLI (never repeated) and is otherwise ignored, so logging can never
take down the development server.
"""

import json
import os
import platform
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from drafter.version import CURRENT_DRAFTER_VERSION

DEBUG_LOG_FILENAME = "drafter-debug.log"
"""Name of the shared debug log, created next to the student's main file."""

MAX_LOG_BYTES = 10 * 1024 * 1024
"""Trim the log once it grows past this many bytes."""

TRIM_TARGET_BYTES = 5 * 512 * 1024
"""When trimming, keep (roughly) this many bytes of the newest entries."""

_write_failure_announced = False
"""Whether the one-time CLI message about a failed log write was printed."""


def get_debug_log_path(directory: Path) -> Path:
    """Return the path of the shared debug log inside the given folder."""
    return Path(directory) / DEBUG_LOG_FILENAME


def build_log_entry(client_payload: Any, main_filename: str) -> dict:
    """Assemble one debug-log entry from a browser error report.

    Combines the client's report (error envelopes plus its environment
    details, mirroring the bug-report bundle) with the server-side
    environment details the browser cannot know.

    Args:
        client_payload: The JSON body the browser posted (kept as-is).
        main_filename: Name of the site's main file, identifying which of
            the folder's sites produced the entry.

    Returns:
        A JSON-serializable dictionary describing the report.
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "main_file": main_filename,
        "server": {
            "drafter_version": CURRENT_DRAFTER_VERSION,
            "python_version": sys.version,
            "platform": platform.platform(),
        },
        "client": client_payload,
    }


def append_error_log_entry(directory: Path, entry: dict) -> bool:
    """Append one entry to the folder's shared debug log.

    The entry is serialized as a single JSON line and appended; the log is
    then trimmed if it has grown too large. All failures are swallowed: the
    first one prints a single CLI message, later ones are silent.

    Args:
        directory: Folder holding the log (the student's code folder).
        entry: JSON-serializable entry, normally from ``build_log_entry``.

    Returns:
        True if the entry was written, False otherwise.
    """
    global _write_failure_announced
    path = get_debug_log_path(directory)
    try:
        line = json.dumps(entry, default=str)
        with open(path, "a", encoding="utf-8") as log_file:
            log_file.write(line + "\n")
    except Exception as error:
        if not _write_failure_announced:
            _write_failure_announced = True
            print(
                f"Drafter could not write to its debug log ({path}): {error}. "
                "Further failures will not be reported."
            )
        return False
    _trim_log_if_needed(path)
    return True


def _trim_log_if_needed(path: Path) -> None:
    """Trim the log down to its newest entries once it grows too large.

    Keeps whole lines from the end of the file until ``TRIM_TARGET_BYTES``
    is reached, then atomically replaces the log (a temp file in the same
    folder plus ``os.replace``), so concurrent readers never see a partial
    file. Trimming is best-effort: any failure (including losing the
    replace race to another dev server) leaves the log as-is for the next
    append to retry.
    """
    try:
        if path.stat().st_size <= MAX_LOG_BYTES:
            return
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines(
            keepends=True
        )
        kept: list[str] = []
        kept_size = 0
        for line in reversed(lines):
            kept_size += len(line.encode("utf-8"))
            if kept_size > TRIM_TARGET_BYTES:
                break
            kept.append(line)
        kept.reverse()
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=path.name + ".", dir=str(path.parent)
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as temporary_file:
                temporary_file.writelines(kept)
            os.replace(temporary_name, path)
        except Exception:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass
            raise
    except Exception:
        pass
