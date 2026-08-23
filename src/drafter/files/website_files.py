"""Validation for files that a Drafter site links into every page.

`add_website_css_file()`, `add_website_js_file()`, and `add_website_file()`
in `drafter.deploy` accept either a full URL or the path of a file that
lives next to the student's program. URLs are taken on trust, but a local
path is checked right away, while the student is still looking at the line
that named it: a missing file raises a `StudentFacingError` that explains
where Drafter looked and suggests similarly named files from that folder
(a `styles.css` when they asked for `style.css`, a file with different
capitalization, or the same name inside a subfolder).

The check adapts to where the code is running. Outside the browser, paths
resolve against the configured user directory (see `get_drafter_path`). In
Pyodide, the file may already sit in the instance's virtual folder, or it
may live on the development server, which is asked for a directory listing
through its `LIST_FILES` route. When neither the file nor a listing can be
reached (e.g. a deployed site without the dev server), the path is accepted
as-is rather than blocking the site on an unverifiable guess.
"""

from __future__ import annotations

import difflib
import json
import os
import pathlib

from drafter.config.urls import INTERNAL_ROUTES
from drafter.data.errors import StudentFacingError
from drafter.helpers.utils import is_pyodide, is_web

#: File kinds (and their accepted extensions) that the link helpers verify.
EXPECTED_EXTENSIONS: dict[str, tuple[str, ...]] = {
    "css": (".css",),
    "js": (".js", ".mjs"),
}

#: The most similarly named files to mention in an error.
MAX_SUGGESTIONS = 3
#: How many entries a directory listing will be scanned for suggestions.
MAX_LISTED_ENTRIES = 2000
#: How deep the subfolder search for an exact filename goes.
MAX_SUBFOLDER_DEPTH = 2
#: Folders never searched for a misplaced file.
SKIPPED_FOLDERS = ("node_modules", "venv", "dist", "site", "build")


def is_url(path: str) -> bool:
    """Whether the path is a URL rather than a file next to the program.

    Args:
        path: The string given by the student.

    Returns:
        True for `http://`, `https://`, protocol-relative `//`, `data:`,
        and `blob:` URLs.
    """
    path = path.strip()
    return "://" in path or path.startswith(("//", "data:", "blob:"))


def normalize_website_path(path: str) -> str:
    """Normalize a relative file path for use in a URL.

    Backslashes (a habit from Windows paths) become forward slashes, and a
    leading `./` is dropped, so `.\\static\\style.css` becomes
    `static/style.css`.

    Args:
        path: The relative path as the student wrote it.

    Returns:
        The cleaned, forward-slash path.
    """
    cleaned = path.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def looks_like_code(path: str) -> bool:
    """Guess whether a "path" is really CSS or JavaScript source code.

    Students sometimes hand `add_website_css_file` the rule they meant to
    give `add_website_css`. Real file names never contain braces, newlines,
    or semicolons, so any of those means the argument is code.

    Args:
        path: The argument to inspect.

    Returns:
        True when the argument looks like source code instead of a name.
    """
    return any(marker in path for marker in ("{", "}", "\n", ";"))


def _user_directory() -> pathlib.Path:
    """The folder that relative paths resolve against outside the browser."""
    from drafter.configuration import get_system_configuration

    try:
        user_directory = get_system_configuration().bootstrap.get_user_directory()
    except ValueError:
        return pathlib.Path.cwd()
    if not user_directory:  # pragma: no cover - defensive
        return pathlib.Path.cwd()
    return pathlib.Path(user_directory)


def _instance_directory() -> pathlib.Path | None:
    """The Pyodide instance's virtual folder, when one is configured."""
    from drafter.client_server.commands import get_current_instance_root

    root = get_current_instance_root()
    if root is None:
        return None
    return pathlib.Path(root)


def list_directory_entries(directory: pathlib.Path) -> list[str]:
    """Names of the entries in a real (or Pyodide-virtual) directory.

    Directories are suffixed with "/" so callers can tell them apart.

    Args:
        directory: The folder to list.

    Returns:
        Sorted entry names (at most `MAX_LISTED_ENTRIES`), or an empty list
        when the directory cannot be read.
    """
    try:
        entries = sorted(os.listdir(directory))[:MAX_LISTED_ENTRIES]
    except OSError:
        return []
    names = []
    for name in entries:
        if os.path.isdir(directory / name):
            names.append(name + "/")
        else:
            names.append(name)
    return names


def find_in_subfolders(directory: pathlib.Path, filename: str) -> list[str]:
    """Relative paths of files named `filename` inside nearby subfolders.

    Walks at most `MAX_SUBFOLDER_DEPTH` levels below `directory`, skipping
    hidden folders and common tool folders, so a student who saved
    `style.css` inside `static/` is pointed at `static/style.css`.

    Args:
        directory: The folder to search below.
        filename: The bare file name to look for (case-insensitive).

    Returns:
        Up to `MAX_SUGGESTIONS` forward-slash paths relative to `directory`.
    """
    found: list[str] = []
    wanted = filename.lower()
    base_depth = len(pathlib.Path(directory).parts)
    try:
        for root, dirs, files in os.walk(directory):
            depth = len(pathlib.Path(root).parts) - base_depth
            dirs[:] = sorted(
                d
                for d in dirs
                if not d.startswith((".", "_")) and d not in SKIPPED_FOLDERS
            )
            if depth + 1 >= MAX_SUBFOLDER_DEPTH:
                dirs[:] = []
            if depth == 0:
                continue
            for name in files:
                if name.lower() == wanted:
                    relative = pathlib.Path(root, name).relative_to(directory)
                    found.append(relative.as_posix())
            if len(found) >= MAX_SUGGESTIONS:
                break
    except OSError:
        pass
    return found[:MAX_SUGGESTIONS]


def find_similar_files(name: str, candidates: list[str]) -> list[str]:
    """Pick the candidate names most likely to be what the student meant.

    Exact matches ignoring case come first (a capitalization slip), then
    names that share the stem but differ in extension, then close spellings
    according to `difflib` (checked both case-sensitively and ignoring
    case).

    Args:
        name: The file name the student asked for (no folders).
        candidates: Entry names from the folder that was searched
            (directories end in "/").

    Returns:
        Up to `MAX_SUGGESTIONS` names, best first, without duplicates and
        never the name itself.
    """
    suggestions: list[str] = []

    def add(candidate: str) -> None:
        if candidate not in suggestions and candidate != name:
            suggestions.append(candidate)

    lowered = name.lower()
    stem = pathlib.PurePosixPath(name).stem.lower()
    for candidate in candidates:
        if candidate.lower() == lowered:
            add(candidate)
    for candidate in candidates:
        if (
            not candidate.endswith("/")
            and pathlib.PurePosixPath(candidate).stem.lower() == stem
        ):
            add(candidate)
    for candidate in difflib.get_close_matches(
        name, candidates, n=MAX_SUGGESTIONS, cutoff=0.6
    ):
        add(candidate)
    by_lower = {candidate.lower(): candidate for candidate in candidates}
    for candidate in difflib.get_close_matches(
        lowered, list(by_lower), n=MAX_SUGGESTIONS, cutoff=0.6
    ):
        add(by_lower[candidate])
    return suggestions[:MAX_SUGGESTIONS]


def _fetch_server_listing(subfolder: str) -> list[str] | None:
    """Ask the development server for a folder listing (Pyodide only).

    Returns None when the listing route is unreachable (a deployed site,
    or a server that does not serve the student's files).
    """
    try:
        from js import XMLHttpRequest  # type: ignore[import-not-found]

        url = INTERNAL_ROUTES["LIST_FILES"]
        if subfolder:
            url += f"?path={subfolder}"
        req = XMLHttpRequest.new()
        req.open("GET", url, False)
        req.send()
        if req.status != 200:
            return None
        payload = json.loads(str(req.responseText))
        entries = (
            payload.get("entries", payload) if isinstance(payload, dict) else payload
        )
        names = []
        for entry in entries:
            if isinstance(entry, dict):
                entry_name = str(entry.get("name", ""))
                if entry.get("is_dir"):
                    entry_name += "/"
                names.append(entry_name)
            else:
                names.append(str(entry))
        return names
    except Exception:
        return None


def _server_has_file(path: str) -> bool | None:
    """Check with the page's server whether a file exists (Pyodide only).

    Returns True/False from the HTTP status, or None if the request could
    not be made at all (or answered with something other than 200/404).
    """
    try:
        from js import XMLHttpRequest  # type: ignore[import-not-found]

        req = XMLHttpRequest.new()
        req.open("HEAD", path, False)
        req.send()
        if req.status == 200:
            return True
        if req.status == 404:
            return False
        return None
    except Exception:
        return None


class WebsiteFileLookup:
    """Where a website file was looked for, and what was found nearby.

    Attributes:
        exists: True if the file was found, False if it is definitely
            missing, None if this environment cannot tell.
        searched_in: Human-readable description of the folder searched.
        siblings: Entry names found in the folder the file should be in.
        in_subfolders: Relative paths of same-named files in subfolders.
    """

    def __init__(self) -> None:
        self.exists: bool | None = None
        self.searched_in: str = "the folder containing your program"
        self.siblings: list[str] = []
        self.in_subfolders: list[str] = []


def lookup_website_file(path: str) -> WebsiteFileLookup:
    """Look for a relative file path in the student's program folder.

    Args:
        path: A normalized relative path such as `style.css` or
            `static/style.css`.

    Returns:
        A `WebsiteFileLookup` describing whether it exists and what
        similarly placed files were found for suggestions.
    """
    result = WebsiteFileLookup()
    relative = pathlib.PurePosixPath(path)
    subfolder = relative.parent.as_posix()
    if subfolder == ".":
        subfolder = ""

    if is_pyodide():
        instance_dir = _instance_directory()
        if instance_dir is not None:
            if (instance_dir / path).exists():
                result.exists = True
                return result
            result.siblings = list_directory_entries(instance_dir / subfolder)
            result.in_subfolders = find_in_subfolders(instance_dir, relative.name)
        # Not in the virtual filesystem: the dev server may still serve it.
        served = _server_has_file(path)
        if served is True:
            result.exists = True
            return result
        listing = _fetch_server_listing(subfolder)
        if listing is not None:
            result.siblings = result.siblings + [
                name for name in listing if name not in result.siblings
            ]
            result.exists = relative.name in listing if served is None else served
        elif served is False:
            result.exists = False
        # Otherwise exists stays None: nothing here can check.
        return result

    if is_web():
        # Other web runtimes (Skulpt) have no file access to check against.
        return result

    base = _user_directory()
    result.searched_in = str(base)
    target = base / pathlib.Path(path)
    result.exists = target.is_file()
    if not result.exists:
        result.siblings = list_directory_entries(target.parent)
        result.in_subfolders = find_in_subfolders(base, relative.name)
    return result


def missing_file_error(
    function_name: str, path: str, lookup: WebsiteFileLookup
) -> StudentFacingError:
    """Build the student-facing error for a file that could not be found.

    Args:
        function_name: The helper that was called (for the message).
        path: The normalized relative path that was not found.
        lookup: What `lookup_website_file` found nearby.

    Returns:
        The error to raise, with "Did you mean" suggestions in its steps.
    """
    relative = pathlib.PurePosixPath(path)
    suggestions = find_similar_files(relative.name, lookup.siblings)
    folder = relative.parent.as_posix()
    if folder != ".":
        suggestions = [f"{folder}/{s}" for s in suggestions]
    steps: list[str] = [f"Did you mean '{suggestion}'?" for suggestion in suggestions]
    for nested in lookup.in_subfolders:
        if nested not in suggestions and nested != path:
            steps.append(
                f"A file named '{relative.name}' exists at '{nested}'. "
                f"If that is the one you want, use {function_name}('{nested}')."
            )
    steps.append(
        "Make sure the file is saved in the same folder as your Python program"
        " (or give its path relative to that folder)."
    )
    steps.append(
        "Check the spelling and capitalization of the name; it must match the"
        " file exactly."
    )
    friendly = (
        f"Drafter looked for a file named '{path}' in {lookup.searched_in},"
        " but there is no file with that name."
    )
    if suggestions:
        friendly += f" Similar names in that folder: {', '.join(suggestions)}."
    return StudentFacingError(
        f"{function_name}: file not found: {path!r} (searched in {lookup.searched_in})",
        friendly=friendly,
        steps=steps,
        title="Website File Not Found",
    )


def resolve_website_file(path: str, function_name: str, kind: str = "file") -> str:
    """Validate a path or URL given to one of the `add_website_*` helpers.

    Args:
        path: The student's argument: a full URL, or the path of a file
            next to their program.
        function_name: The helper's name, used in error messages.
        kind: "css", "js", or "file"; CSS and JS paths must have a matching
            extension (URLs are not checked, since a stylesheet URL may have
            no extension at all).

    Returns:
        The URL unchanged (stripped), or the normalized relative path
        (forward slashes, no leading `./`).

    Raises:
        StudentFacingError: If the argument is not a string, is empty, looks
            like code rather than a name, is an absolute path, escapes the
            program folder, has the wrong extension, or names a file that
            does not exist.
    """
    if not isinstance(path, str):
        raise StudentFacingError(
            f"{function_name}: expected a string path or URL, got"
            f" {type(path).__name__}",
            friendly=(
                f"{function_name} needs the name of a file (like 'style.css') or a"
                f" full URL, written as a string, but it was given a"
                f" {type(path).__name__}."
            ),
            steps=(f"Call it like {function_name}('style.css').",),
            title="Website File Path Must Be a String",
        )
    if not path.strip():
        raise StudentFacingError(
            f"{function_name}: the path is empty",
            friendly=(
                f"{function_name} was given an empty string, so there is no file"
                " to add."
            ),
            steps=(f"Give it the name of a file, like {function_name}('style.css').",),
            title="Website File Path Is Empty",
        )
    if kind in EXPECTED_EXTENSIONS and looks_like_code(path):
        language = "CSS" if kind == "css" else "JavaScript"
        inline_helper = "add_website_css" if kind == "css" else "add_website_js"
        raise StudentFacingError(
            f"{function_name}: expected a file path or URL, but the argument looks"
            f" like {language} code",
            friendly=(
                f"{function_name} expects the name of a {language} file (or a URL),"
                f" but it was given what looks like {language} code."
            ),
            steps=(
                f"To add {language} written directly in your program, use"
                f" {inline_helper}(...) instead.",
                f"To add a {language} file, save the code in a file next to your"
                f" program and pass its name: {function_name}('style.{kind}').",
            ),
            title=f"{language} Code Given Instead of a File",
        )
    if is_url(path):
        return path.strip()

    normalized = normalize_website_path(path)
    pure = pathlib.PurePosixPath(normalized)
    if pathlib.PureWindowsPath(path.strip()).is_absolute() or normalized.startswith(
        "/"
    ):
        raise StudentFacingError(
            f"{function_name}: absolute paths are not supported: {path!r}",
            friendly=(
                f"The path '{path}' is an absolute path (it starts from the root of"
                " your computer). A website can only use files that live next"
                " to your program, since those are the files that get published"
                " with it."
            ),
            steps=(
                "Move the file into the same folder as your Python program.",
                f"Then use just its name: {function_name}('{pure.name}').",
            ),
            title="Website File Must Be Next to Your Program",
        )
    if ".." in pure.parts:
        raise StudentFacingError(
            f"{function_name}: path leaves the program folder: {path!r}",
            friendly=(
                f"The path '{path}' points outside the folder that holds your"
                " program. A website can only use files inside that folder,"
                " since those are the files that get published with it."
            ),
            steps=(
                "Move the file into the same folder as your Python program"
                " (or a subfolder of it).",
                "Then use a path relative to that folder:"
                f" {function_name}('{pure.name}').",
            ),
            title="Website File Must Be Next to Your Program",
        )
    if kind in EXPECTED_EXTENSIONS:
        allowed = EXPECTED_EXTENSIONS[kind]
        if pure.suffix.lower() not in allowed:
            language = "CSS" if kind == "css" else "JavaScript"
            expected = " or ".join(allowed)
            ending = f"'{pure.suffix}'" if pure.suffix else "nothing"
            raise StudentFacingError(
                f"{function_name}: expected a {language} file ending in {expected},"
                f" got {path!r}",
                friendly=(
                    f"{function_name} adds {language} files, which end in"
                    f" {expected}, but '{path}' ends in {ending}."
                ),
                steps=(
                    f"If the file really contains {language}, rename it to end in"
                    f" {allowed[0]} and update this call.",
                    "If you meant to add a different kind of file to the site,"
                    " use add_website_file(...) instead.",
                ),
                title=f"Not a {language} File",
            )

    lookup = lookup_website_file(normalized)
    if lookup.exists is False:
        raise missing_file_error(function_name, normalized, lookup)
    return normalized
