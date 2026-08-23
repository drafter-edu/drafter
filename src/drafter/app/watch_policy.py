"""Decides which paths the development server watches for live reload.

The default behavior is to watch the student's main file and to recursively
watch its parent directory, exactly as before. Before establishing that
recursive watch, however, this module performs a set of safety checks: the
directory must not be a filesystem root, the user's home directory, or a
known broad location (Desktop, Documents, Downloads, ...), and a bounded scan
must stay within configured file-count, directory-count, and depth limits.

When a check fails, Drafter switches to *safe mode*: it watches the main
file, any explicitly configured paths, and entries from the optional watch
manifest, and (elsewhere, at serve time) dynamically adds files the server
actually serves. This keeps live reload working for students who run their
program from a giant folder like Downloads without watchfiles trying to
index tens of thousands of files.

All of the policy is driven by settings on
:class:`drafter.config.app_server.AppServerConfiguration` rather than fixed
heuristics; see that class for the available knobs.
"""

import fnmatch
import json
import os
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from watchfiles import DefaultFilter

from drafter.app.error_log import DEBUG_LOG_FILENAME
from drafter.app.source_recovery import UNSAVED_SOURCE_FILENAME
from drafter.app.watcher import WatchedPath
from drafter.config.app_server import AppServerConfiguration
from drafter.config.system import SystemConfiguration

DRAFTER_GENERATED_FILENAMES = frozenset({DEBUG_LOG_FILENAME, UNSAVED_SOURCE_FILENAME})
"""Files Drafter itself writes at runtime; they must never trigger reloads."""

BROAD_LOCATION_NAMES = frozenset(
    {"desktop", "documents", "my documents", "downloads", "onedrive", "dropbox"}
)
"""Lowercased folder names that count as broad locations when under home."""

SCAN_IGNORED_DIRECTORIES = frozenset(DefaultFilter.ignore_dirs)
"""Directories skipped by the safety scan; watchfiles ignores their events
anyway (e.g. .git, __pycache__, node_modules), so their size is irrelevant."""

_GLOB_CHARS = ("*", "?", "[")


@dataclass
class IgnoreRules:
    """Drafter-specific rules for changes that must never trigger a reload.

    Applied on top of watchfiles' own default filter. Covers both
    Drafter-generated runtime files and user-configured ignore patterns.

    Attributes:
        base_directory: Resolved directory that relative patterns (like
            "output/" or "data/*.tmp") are matched against.
        patterns: Ignore patterns: a bare name or glob matches the filename
            or the path relative to `base_directory`; a pattern ending in
            "/" ignores that whole directory subtree.
        generated_names: Exact filenames that are always ignored.
    """

    base_directory: Path
    patterns: tuple[str, ...] = ()
    generated_names: frozenset[str] = DRAFTER_GENERATED_FILENAMES

    def should_ignore(self, path: Path | str) -> bool:
        """Decide whether a changed path should be ignored.

        Args:
            path: The changed path (absolute or relative).

        Returns:
            True when the change must not trigger a reload.
        """
        path = Path(path)
        if path.name in self.generated_names:
            return True
        if not self.patterns:
            return False
        try:
            relative = path.resolve().relative_to(self.base_directory).as_posix()
        except (ValueError, OSError):
            relative = None
        for pattern in self.patterns:
            normalized = str(pattern).replace("\\", "/").strip()
            if not normalized:
                continue
            if normalized.endswith("/"):
                prefix = normalized.rstrip("/")
                if relative is not None and (
                    relative == prefix or relative.startswith(prefix + "/")
                ):
                    return True
                continue
            if fnmatch.fnmatch(path.name, normalized):
                return True
            if relative is not None and fnmatch.fnmatch(relative, normalized):
                return True
        return False


@dataclass
class WatchPlan:
    """The outcome of applying the watch policy to a project.

    Attributes:
        paths: The static paths to watch (files and directories).
        safe_mode: Whether adjacent-file watching fell back to safe mode
            (no recursive watch of the main file's directory).
        safe_mode_reason: Human-readable reason a safety check failed, set
            only when safe mode was entered *automatically*; None when safe
            mode was requested through configuration (or not entered).
        track_served_files: Whether files the server actually serves should
            be dynamically added to the watch set.
        ignore_rules: Drafter-specific ignore rules for the watcher.
        warnings: Non-fatal problems (e.g. an unreadable manifest) for the
            caller to surface.
    """

    paths: list[WatchedPath]
    safe_mode: bool = False
    safe_mode_reason: str | None = None
    track_served_files: bool = False
    ignore_rules: IgnoreRules | None = None
    warnings: list[str] = field(default_factory=list)


def is_broad_location(directory: Path, home: Path) -> bool:
    """Check whether a directory is a known broad location under home.

    Matches Desktop/Documents/Downloads-style folders directly under the
    home directory, including the common cloud-synced nesting one level
    deeper (e.g. ``~/OneDrive/Documents``).

    Args:
        directory: Resolved directory to test.
        home: Resolved home directory.

    Returns:
        True when the directory is a broad location.
    """
    if directory.name.lower() not in BROAD_LOCATION_NAMES:
        return False
    if directory.parent == home:
        return True
    return (
        directory.parent.parent == home
        and directory.parent.name.lower() in BROAD_LOCATION_NAMES
    )


def scan_exceeds_limits(
    directory: Path,
    max_files: int | None,
    max_directories: int | None,
    max_depth: int | None,
) -> str | None:
    """Scan a directory tree, stopping as soon as a resource limit is hit.

    Directories that watchfiles ignores by default (.git, __pycache__, ...)
    are skipped, since their contents never produce reload events. The scan
    aborts (and reports the directory as too large) the moment any limit is
    exceeded, so it stays cheap even inside enormous folders.

    Args:
        directory: The directory to scan.
        max_files: Maximum number of files, or None for no limit.
        max_directories: Maximum number of subdirectories, or None for no
            limit.
        max_depth: Maximum nesting depth (children of `directory` are at
            depth 1), or None for no limit.

    Returns:
        A human-readable reason string when a limit is exceeded, else None.
    """
    if max_files is None and max_directories is None and max_depth is None:
        return None
    file_count = 0
    directory_count = 0
    pending: list[tuple[Path, int]] = [(directory, 0)]
    while pending:
        current, depth = pending.pop()
        if max_depth is not None and depth > max_depth:
            return f"it contains folders nested more than {max_depth} levels deep"
        try:
            entries = list(os.scandir(current))
        except OSError:
            continue
        for entry in entries:
            try:
                is_directory = entry.is_dir(follow_symlinks=False)
            except OSError:
                continue
            if is_directory:
                if entry.name in SCAN_IGNORED_DIRECTORIES:
                    continue
                directory_count += 1
                if max_directories is not None and directory_count > max_directories:
                    return f"it contains more than {max_directories} folders"
                pending.append((Path(entry.path), depth + 1))
            else:
                file_count += 1
                if max_files is not None and file_count > max_files:
                    return f"it contains more than {max_files} files"
    return None


def describe_unsafe_directory(
    directory: Path,
    config: AppServerConfiguration,
    home: Path | None = None,
) -> str | None:
    """Run the safety checks that guard recursive watching.

    Args:
        directory: The directory that would be watched recursively.
        config: The app server configuration providing limits and toggles.
        home: The user's home directory; defaults to Path.home() (kept as a
            parameter for testing).

    Returns:
        A human-readable reason the directory is unsafe to watch
        recursively, or None when every check passes.
    """
    try:
        directory = Path(directory).resolve()
    except OSError:
        return "its location could not be determined"
    if directory.parent == directory:
        return "it is a filesystem root"
    try:
        home = (home or Path.home()).resolve()
    except (OSError, RuntimeError):
        home = None
    if home is not None:
        if directory == home:
            return "it is your home directory"
        if not config.watch_broad_locations and is_broad_location(directory, home):
            return f"it is a commonly shared folder ({directory.name})"
    return scan_exceeds_limits(
        directory,
        config.watch_max_files,
        config.watch_max_directories,
        config.watch_max_depth,
    )


def load_watch_manifest(
    manifest_path: Path,
) -> tuple[list[str], list[str], str | None]:
    """Load a watch manifest JSON file.

    Two shapes are accepted: a plain list of watch entries, or an object
    with "watch_paths" and "ignore_watch_paths" lists. Entries may be file
    paths, directories (watched recursively), or glob patterns.

    Args:
        manifest_path: Path to the JSON manifest file.

    Returns:
        A (watch_entries, ignore_entries, error) tuple; on any problem the
        entry lists are empty and `error` describes what went wrong.
    """
    try:
        data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [], [], f"Could not read watch manifest {manifest_path}: {error}"
    if isinstance(data, list):
        watch_entries, ignore_entries = data, []
    elif isinstance(data, dict):
        watch_entries = data.get("watch_paths", [])
        ignore_entries = data.get("ignore_watch_paths", [])
    else:
        return (
            [],
            [],
            f"Watch manifest {manifest_path} must be a JSON list or object",
        )
    if not isinstance(watch_entries, list) or not isinstance(ignore_entries, list):
        return (
            [],
            [],
            f"Watch manifest {manifest_path} entries must be JSON lists",
        )
    return (
        [str(entry) for entry in watch_entries],
        [str(entry) for entry in ignore_entries],
        None,
    )


def resolve_watch_entries(
    entries: Sequence[str | Path], base_directory: Path
) -> list[Path]:
    """Turn configured watch entries into concrete paths.

    Glob entries are expanded relative to `base_directory` at call time;
    plain entries are resolved against it (absolute entries pass through).
    Directories are returned as-is and end up watched recursively.

    Args:
        entries: Watch entries: files, directories, or glob patterns.
        base_directory: Directory relative entries are resolved against.

    Returns:
        The list of concrete paths (which may include nonexistent ones;
        callers decide whether to skip those).
    """
    resolved: list[Path] = []
    for entry in entries:
        text = str(entry)
        if any(character in text for character in _GLOB_CHARS):
            try:
                resolved.extend(sorted(base_directory.glob(text)))
            except (ValueError, OSError, NotImplementedError):
                continue
            continue
        path = Path(text)
        if not path.is_absolute():
            path = base_directory / path
        resolved.append(path)
    return resolved


def build_watch_plan(
    system: SystemConfiguration,
    user_directory: Path,
    user_path: Path,
    main_file_on_disk: bool,
    home: Path | None = None,
) -> WatchPlan:
    """Apply the watch policy and produce the plan for the dev server.

    Args:
        system: The system configuration (app_server section drives policy).
        user_directory: The directory containing the student's main file.
        user_path: The student's main file.
        main_file_on_disk: Whether the main file actually exists on disk
            (False when the source was recovered from memory, in which case
            there is no file to watch or to re-read on restart).
        home: Home-directory override for the safety checks (testing hook).

    Returns:
        The resulting WatchPlan.
    """
    config = system.app_server
    user_directory = Path(user_directory).resolve()
    warnings: list[str] = []

    # Manifest entries: relative paths resolve against the manifest's folder.
    manifest_watch: list[str] = []
    manifest_ignore: list[str] = []
    manifest_base = user_directory
    if config.watch_manifest:
        manifest_path = Path(config.watch_manifest)
        if not manifest_path.is_absolute():
            manifest_path = user_directory / manifest_path
        manifest_base = manifest_path.parent
        manifest_watch, manifest_ignore, manifest_error = load_watch_manifest(
            manifest_path
        )
        if manifest_error:
            warnings.append(manifest_error)

    ignore_rules = IgnoreRules(
        base_directory=user_directory,
        patterns=tuple(
            str(pattern)
            for pattern in [*(config.ignore_watch_paths or []), *manifest_ignore]
        ),
    )

    paths: list[WatchedPath] = []
    # Matches the historical behavior: when the main file exists, changes to
    # project files re-push the student's code (full_reload=False); with
    # in-memory source there is nothing to re-read, so only reload the page.
    full_reload_default = not main_file_on_disk
    if main_file_on_disk:
        paths.append(WatchedPath(Path(user_path), False))

    safe_mode = False
    safe_mode_reason: str | None = None
    if config.watch_adjacent_files:
        if not config.watch_recursively:
            safe_mode = True
        elif config.watch_force_recursive or not config.watch_safe_mode:
            paths.append(WatchedPath(user_directory, full_reload_default))
        else:
            safe_mode_reason = describe_unsafe_directory(
                user_directory, config, home=home
            )
            if safe_mode_reason is None:
                paths.append(WatchedPath(user_directory, full_reload_default))
            else:
                safe_mode = True

    # Explicit paths and manifest entries apply regardless of safe mode.
    entry_paths = resolve_watch_entries(list(config.watch_paths or []), user_directory)
    entry_paths.extend(resolve_watch_entries(manifest_watch, manifest_base))
    for entry_path in entry_paths:
        if entry_path.exists():
            paths.append(WatchedPath(entry_path, full_reload_default))

    # Deduplicate while keeping the first (highest-priority) entry per path.
    seen: set[Path] = set()
    unique_paths: list[WatchedPath] = []
    for watched in paths:
        try:
            key = watched.directory.resolve()
        except OSError:
            key = watched.directory
        if key in seen:
            continue
        seen.add(key)
        unique_paths.append(WatchedPath(key, watched.full_reload))

    return WatchPlan(
        paths=unique_paths,
        safe_mode=safe_mode,
        safe_mode_reason=safe_mode_reason,
        track_served_files=safe_mode and config.watch_served_files,
        ignore_rules=ignore_rules,
        warnings=warnings,
    )


def safe_mode_notice(main_filename: str) -> str:
    """Build the message shown when safe mode is entered automatically.

    Args:
        main_filename: The name of the student's main file.

    Returns:
        The multi-line notice to print.
    """
    return (
        f"Drafter noticed that {main_filename} is in a large or broad folder.\n"
        "For safety, live reload will watch your program and files used by\n"
        "your site rather than the entire folder."
    )
