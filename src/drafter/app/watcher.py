"""File watching and live reload functionality.

Monitors file changes and broadcasts reload events to connected WebSocket clients,
enabling live reload during development.
"""

import asyncio
import contextlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from starlette.websockets import WebSocket
from watchfiles import Change, DefaultFilter, awatch

from drafter.app.error_log import DEBUG_LOG_FILENAME
from drafter.config.system import SystemConfiguration

if TYPE_CHECKING:
    from drafter.app.watch_policy import IgnoreRules


@dataclass
class WatchedPath:
    """Represents a file system path to be watched for changes.

    Attributes:
        directory: The file system path to watch.
        full_reload: Whether to trigger a full page reload when changes are detected in this path, or just restart the code.
    """

    directory: Path
    full_reload: bool = True


class ReloadHub:
    """Manages WebSocket connections and broadcasts reload events.

    Tracks connected WebSocket clients and sends reload messages when
    watched files change.

    Attributes:
        _clients: Set of active WebSocket connections.
        _lock: Asyncio lock for thread-safe client management.
    """

    def __init__(self) -> None:
        """Initialize empty client set and lock."""
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def register(self, ws: WebSocket) -> None:
        """Register a new WebSocket connection.

        Args:
            ws: WebSocket connection to register.
        """
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    async def unregister(self, ws: WebSocket) -> None:
        """Unregister a WebSocket connection.

        Args:
            ws: WebSocket connection to remove.
        """
        async with self._lock:
            self._clients.discard(ws)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a message to all connected clients.

        Removes dead connections from the client set.
        """
        payload = json.dumps(message)
        async with self._lock:
            dead: list[WebSocket] = []
            for ws in self._clients:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._clients.discard(ws)

    async def broadcast_reload(self) -> None:
        """Send a full page reload message to all connected clients."""
        await self.broadcast({"type": "reload"})

    async def broadcast_student_restart(self, code: str) -> None:
        """Send a student-code restart message to all connected clients."""
        await self.broadcast({"type": "restart_student_code", "code": code})


async def ws_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live reload connections.

    Accepts a connection, registers it, and keeps it open until closed.

    Args:
        websocket: Starlette WebSocket object.
    """
    hub: ReloadHub = websocket.app.state.hub  # type: ignore
    await hub.register(websocket)
    try:
        while True:
            # Keep the connection alive; client doesn't need to send messages
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        await hub.unregister(websocket)


async def _read_student_code(student_path: Path, attempts: int = 5) -> str:
    """Read the student's code file, retrying transient failures.

    Editors (especially on Windows) briefly lock or truncate the file
    mid-save, so the first read after a change event can fail or return a
    partial file. Retries with a short delay before giving up.

    Args:
        student_path: Path to the student's main code file.
        attempts: Maximum number of read attempts.

    Returns:
        The file contents.

    Raises:
        OSError: If the file still cannot be read after all attempts.
    """
    last_error: OSError | None = None
    for attempt in range(attempts):
        try:
            return student_path.read_text(encoding="utf-8")
        except OSError as error:
            last_error = error
            await asyncio.sleep(0.1 * (attempt + 1))
    raise last_error if last_error else OSError("Could not read student code")


class DrafterWatchFilter(DefaultFilter):
    """watchfiles filter combining the defaults with Drafter's ignore rules.

    On top of watchfiles' DefaultFilter (which skips .git, __pycache__,
    editor temp files, etc.), this drops changes to Drafter-generated
    runtime files (like the shared debug log) and user-configured ignore
    patterns, so they can never trigger a reload.
    """

    def __init__(self, ignore_rules: "IgnoreRules | None" = None) -> None:
        """Initialize with optional Drafter-specific ignore rules.

        Args:
            ignore_rules: Rules from the watch policy; None applies only
                the watchfiles defaults.
        """
        super().__init__()
        self.ignore_rules = ignore_rules

    def __call__(self, change: Change, path: str) -> bool:
        """Decide whether a change event should be reported.

        Args:
            change: The kind of change (added/modified/deleted).
            path: The changed path.

        Returns:
            True when the change should be reported to the watcher.
        """
        if not super().__call__(change, path):
            return False
        if self.ignore_rules is not None and self.ignore_rules.should_ignore(path):
            return False
        return True


class WatchSet:
    """A mutable set of watched paths that the watcher can react to.

    Holds the static paths from the watch plan and allows new files to be
    added while the server runs (safe mode adds files that were actually
    served). Setting `changed` wakes `_watch_and_reload` so it can restart
    watchfiles over the updated set of roots.

    Attributes:
        ignore_rules: Drafter-specific ignore rules; candidate additions
            matching them are rejected.
        changed: Event set whenever the watch set gains a path.
    """

    def __init__(
        self,
        paths: Iterable[WatchedPath],
        ignore_rules: "IgnoreRules | None" = None,
    ) -> None:
        """Initialize from the watch plan's static paths.

        Args:
            paths: The initial paths to watch.
            ignore_rules: Optional Drafter-specific ignore rules.
        """
        self._paths: dict[Path, WatchedPath] = {}
        self.ignore_rules = ignore_rules
        self.changed = asyncio.Event()
        for watched in paths:
            self.add(watched)

    def add(self, watched: WatchedPath) -> bool:
        """Add a path, keyed by its resolved form; returns True if new."""
        try:
            key = watched.directory.resolve()
        except OSError:
            key = watched.directory
        if key in self._paths:
            return False
        self._paths[key] = WatchedPath(key, watched.full_reload)
        return True

    def add_watched_file(self, path: Path | str, full_reload: bool = False) -> bool:
        """Dynamically add a file to the watch set (e.g., a served file).

        Files that are ignored, missing, or already covered by a watched
        directory are skipped. On success the `changed` event is set so the
        running watcher picks up the new root.

        Args:
            path: The file to start watching.
            full_reload: Whether changes to it should trigger a full page
                reload instead of a student-code restart.

        Returns:
            True when the file was newly added.
        """
        candidate = Path(path)
        if self.ignore_rules is not None and self.ignore_rules.should_ignore(candidate):
            return False
        try:
            resolved = candidate.resolve()
            if not resolved.is_file():
                return False
        except OSError:
            return False
        for existing in self._paths:
            if existing.is_dir() and resolved.is_relative_to(existing):
                return False
        if self.add(WatchedPath(resolved, full_reload)):
            self.changed.set()
            return True
        return False

    def roots(self) -> list[Path]:
        """Return the currently existing paths to hand to watchfiles."""
        return [path for path in self._paths if path.exists()]

    def missing_paths(self) -> list[Path]:
        """Return watched paths that do not currently exist on disk."""
        return [path for path in self._paths if not path.exists()]

    def restart_targets(self) -> set[Path]:
        """Return the paths whose changes trigger a student-code restart."""
        return {
            path for path, watched in self._paths.items() if not watched.full_reload
        }


async def _stop_when_watch_set_changes(
    watch_set: WatchSet, stop_event: asyncio.Event
) -> None:
    """Set `stop_event` once the watch set changes, ending the awatch loop."""
    await watch_set.changed.wait()
    stop_event.set()


async def _recheck_missing_paths(watch_set: WatchSet, delay: float = 2.0) -> None:
    """Wake the watcher when a temporarily missing watched path reappears.

    Editors often save with a delete-and-replace, so a watched file can be
    briefly absent exactly when the awatch loop (re)starts and would then
    be silently dropped from the watch. Poll until it comes back, then set
    the `changed` event so the watcher restarts over the full set of roots.
    """
    while watch_set.missing_paths():
        await asyncio.sleep(delay)
        if any(path.exists() for path in watch_set.missing_paths()):
            watch_set.changed.set()
            return


async def _broadcast_for_changes(
    hub: ReloadHub,
    watch_set: WatchSet,
    changes: set[tuple[Change, str]],
    student_path: Path,
) -> None:
    """Broadcast a restart or reload for a batch of change events.

    When a change falls under a path marked `full_reload=False`, a
    student-restart broadcast carrying the current contents of
    `student_path` is attempted first, falling back to a full page reload
    if reading or broadcasting fails. Changes anywhere else trigger a full
    page reload broadcast.
    """
    changed_paths = {Path(path).resolve() for _, path in changes}
    # The watch filter already drops ignored files, but keep the debug-log
    # guard here as well: the server writes that log whenever the browser
    # reports an error, and reacting to those writes would put the site in
    # a restart loop (restart -> error -> log write -> restart).
    changed_paths = {
        path
        for path in changed_paths
        if path.name != DEBUG_LOG_FILENAME
        and not (
            watch_set.ignore_rules is not None
            and watch_set.ignore_rules.should_ignore(path)
        )
    }
    if not changed_paths:
        return
    restart_paths = watch_set.restart_targets()
    if any(
        changed_path.is_relative_to(restart_path)
        for changed_path in changed_paths
        for restart_path in restart_paths
    ):
        try:
            await hub.broadcast_student_restart(await _read_student_code(student_path))
        except Exception:
            await hub.broadcast_reload()
    else:
        await hub.broadcast_reload()


async def _watch_and_reload(
    hub: ReloadHub,
    watch_set: WatchSet,
    system: SystemConfiguration,
    student_path: Path,
):
    """Monitor file changes and broadcast reload or restart events.

    Watches the paths in `watch_set`. Whenever the watch set changes (a
    served file was added in safe mode), the underlying watchfiles loop is
    restarted over the new set of roots.

    Args:
        hub: ReloadHub instance to broadcast through.
        watch_set: The (possibly growing) set of paths to monitor; each
            entry's `full_reload` flag decides between a page reload and a
            student-code restart.
        system: System configuration (for future use).
        student_path: Path to the student's main code file, whose
            contents are sent with student-restart broadcasts.
    """
    watched_student_path = student_path.resolve()
    watch_filter = DrafterWatchFilter(watch_set.ignore_rules)
    while True:
        watch_set.changed.clear()
        roots = watch_set.roots()
        if not roots:
            # Nothing to watch yet; wait until something is added.
            await watch_set.changed.wait()
            continue
        stop_event = asyncio.Event()
        helpers = [
            asyncio.create_task(_stop_when_watch_set_changes(watch_set, stop_event))
        ]
        if watch_set.missing_paths():
            helpers.append(asyncio.create_task(_recheck_missing_paths(watch_set)))
        try:
            async for changes in awatch(
                *roots, stop_event=stop_event, watch_filter=watch_filter
            ):
                await _broadcast_for_changes(
                    hub, watch_set, changes, watched_student_path
                )
        finally:
            for helper in helpers:
                helper.cancel()
            for helper in helpers:
                with contextlib.suppress(asyncio.CancelledError):
                    await helper
        if not watch_set.changed.is_set():
            # awatch stopped without a watch-set change; shut down quietly.
            break
