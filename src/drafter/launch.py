"""Main entry point for starting Drafter servers.

Provides the start_server() function which routes to either in-browser ClientServer
or local development AppServer based on execution context.
"""

import ast
import linecache
import sys
from difflib import get_close_matches
from pathlib import Path
from typing import Any

from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import get_main_server
from drafter.config.engines import EngineType
from drafter.configuration import get_system_configuration
from drafter.data.errors import (
    CATEGORY_CONFIG,
    SEVERITY_WARNING,
    ErrorDetails,
    StudentFacingError,
    format_student_facing_error,
)
from drafter.data.telemetry import ErrorRecord, TelemetryMetadata
from drafter.helpers.utils import is_web

MaybeBoolStr = bool | str | None
"""Type alias for parameters that accept a bool, a string, or None."""

LEGACY_START_SERVER_OPTIONS = frozenset(
    {
        "backend",
        "cdn_drafter_setup",
        "debug",
        "save_uploaded_files",
        "skulpt",
        "src_image_folder",
        "style",
        "title",
    }
)
"""Options that `start_server` took in Drafter 1 and no longer uses.

They are ignored without a warning, so a program written for Drafter 1
still starts quietly."""

UNKNOWN_OPTION_ERROR_ID = "config.unknown_start_server_option"
"""Stable id of the warning for a `start_server` option Drafter does not have."""

START_SERVER_ONLY_OPTIONS = frozenset({"initial_state", "server", "reloader", "argv"})
"""Parameters of `start_server` that are not settings of their own, offered
alongside the settings when suggesting a correction for a misspelled option."""

CODE_AFTER_START_ERROR_ID = "config.code_after_start_server"
"""Stable id of the warning for statements written after `start_server(...)`."""


def warn_at_startup(
    server: ClientServer,
    error_id: str,
    message: str,
    *,
    title: str,
    friendly: str,
    steps: tuple[str, ...],
    terminal_note: str = "",
) -> None:
    """Report a problem with how a program starts its site, without stopping it.

    On the computer the warning is printed in the terminal. In the browser
    it goes to the debug panel, where it stays listed from page to page.

    Args:
        server: The server being started, whose debug panel gets the
            warning in the browser.
        error_id: Stable, code-like id of the warning.
        message: The warning itself, in one or two sentences.
        title: Short title for the debug panel.
        friendly: Plain-language explanation for the debug panel.
        steps: What to try, for the debug panel.
        terminal_note: Extra sentence printed after the message in the
            terminal, where there is no room for the explanation.
    """
    if not is_web():
        printed = f"{message} {terminal_note}".strip()
        print(f"Warning: {printed}", file=sys.stderr)
        return
    envelope = ErrorDetails(
        id=error_id,
        category=CATEGORY_CONFIG,
        message=message,
        severity=SEVERITY_WARNING,
        friendly_title=title,
        friendly_message=friendly,
        friendly_steps=steps,
    )
    server.event_bus.publish(
        ErrorRecord(
            kind=envelope.id,
            metadata=TelemetryMetadata(source="launch.start_server", level="warning"),
            correlation=envelope.context,
            error=envelope,
        )
    )


def find_unknown_options(
    options: dict[str, Any], setting_names: frozenset[str]
) -> list[str]:
    """Pick out the `start_server` options that Drafter does not have.

    Args:
        options: The extra keyword arguments given to `start_server`.
        setting_names: Every setting name Drafter does have.

    Returns:
        The unknown names, in the order they were written. Options from
        Drafter 1 (`LEGACY_START_SERVER_OPTIONS`) are left out.
    """
    return [
        name
        for name in options
        if name not in setting_names and name not in LEGACY_START_SERVER_OPTIONS
    ]


def suggest_option(name: str, setting_names: frozenset[str]) -> str | None:
    """Find the real `start_server` option closest to a misspelled one.

    Args:
        name: The option as it was written.
        setting_names: Every setting name Drafter does have.

    Returns:
        The most similar real option, or None when nothing is close.
    """
    candidates = sorted(setting_names | START_SERVER_ONLY_OPTIONS)
    matches = get_close_matches(name, candidates, n=1)
    return matches[0] if matches else None


def describe_unknown_option(name: str, setting_names: frozenset[str]) -> str:
    """Write the warning for one unknown `start_server` option.

    Args:
        name: The option as it was written.
        setting_names: Every setting name Drafter does have.

    Returns:
        The warning, with a "Did you mean" suggestion when a real option
        has a similar name.
    """
    message = f"Unknown start_server option {name!r}."
    suggestion = suggest_option(name, setting_names)
    if suggestion is not None:
        message += f" Did you mean {suggestion!r}?"
    return message


def report_unknown_options(
    unknown: list[str], setting_names: frozenset[str], server: ClientServer
) -> None:
    """Warn about `start_server` options that were ignored.

    On the computer the warning is printed in the terminal. In the browser
    it goes to the debug panel. Either way the site still starts.

    Args:
        unknown: The unknown option names.
        setting_names: Every setting name Drafter does have.
        server: The server being started, whose debug panel gets the
            warning in the browser.
    """
    for name in unknown:
        suggestion = suggest_option(name, setting_names)
        first_step = (
            f"Check the spelling of {name!r} in your start_server(...) call."
            if suggestion is None
            else f"Change {name!r} to {suggestion!r} in your start_server(...) call."
        )
        warn_at_startup(
            server,
            UNKNOWN_OPTION_ERROR_ID,
            describe_unknown_option(name, setting_names),
            title="Unknown start_server Option",
            friendly=(
                f"start_server was given an option named {name!r}, but "
                "Drafter has no option with that name, so it was ignored. "
                "The site still started."
            ),
            steps=(first_step, "Remove the option if you do not need it."),
            terminal_note="The option was ignored.",
        )


def find_code_after_call(source: str, call_line: int) -> int | None:
    """Find the first statement written after a call at the top of a file.

    Args:
        source: The text of a Python file.
        call_line: The line of a call in that file (`start_server(...)`).

    Returns:
        The line of the first top-level statement after the one holding
        the call, or None when the call is the last thing in the file.
        Also None when the call is not at the top level of the file (it
        is inside a function, say), since what runs after it then
        depends on who called that function.
    """
    statements = ast.parse(source).body
    for index, statement in enumerate(statements):
        last_line = getattr(statement, "end_lineno", None) or statement.lineno
        if not statement.lineno <= call_line <= last_line:
            continue
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return None
        following = statements[index + 1 :]
        return following[0].lineno if following else None
    return None


def report_code_after_start(
    server: ClientServer, filename: str, call_line: int
) -> None:
    """Warn when a program has statements after its `start_server(...)` call.

    That code does run, but not when a reader of the file would expect:
    on the computer `start_server` does not return until the server
    stops, while in the browser it returns as soon as the first page is
    shown. A file that cannot be read or parsed (code typed at a prompt)
    is skipped.

    Args:
        server: The server being started, whose debug panel gets the
            warning in the browser.
        filename: The file that called `start_server`.
        call_line: The line of that call.
    """
    # linecache holds the text of code that is running, wherever it came
    # from. In the browser the program is run under a file name that is not
    # where its file sits in the virtual file system, so reading that name
    # from disk would find nothing.
    source = "".join(linecache.getlines(filename))
    if not source:
        return
    try:
        next_line = find_code_after_call(source, call_line)
    except (SyntaxError, ValueError):
        return
    if next_line is None:
        return
    name = Path(filename).name
    warn_at_startup(
        server,
        CODE_AFTER_START_ERROR_ID,
        f"{name} has code after start_server(...), starting on line {next_line}.",
        title="Code After start_server",
        friendly=(
            f"Line {next_line} of {name} comes after start_server(...). That "
            "code does not run when you would expect: on your computer it "
            "waits until the server stops, and in the browser it runs right "
            "after the first page appears."
        ),
        steps=(
            "Make start_server(...) the last line of your file.",
            "Move routes, tests, and anything else the site needs above it.",
        ),
        terminal_note=(
            "That code will not run until the server stops. Make "
            "start_server(...) the last line of your file."
        ),
    )


def start_server(
    initial_state=None,
    server=None,
    # ClientServer-specific parameters
    server_name: str | None = None,
    in_debug_mode: bool | None = None,
    framed: bool | None = None,
    theme: str | None = None,
    site_title: str | None = None,
    favicon: str | None = None,
    information: dict | None = None,
    # AppServer-specific parameters
    verbose: bool | None = None,
    asset_directory: MaybeBoolStr = None,
    show_filename_as: MaybeBoolStr = None,
    engine: EngineType | None = None,
    port: int | None = None,
    host: str | None = None,
    prerender_initial_page: bool | None = None,
    open_browser: bool | None = None,
    browser: str | None = None,
    inline_py: bool | None = None,
    use_reloader: bool | None = None,
    pyodide_url: str | None = None,
    pyodide_version: str | None = None,
    pyodide_branch: str | None = None,
    # Aliases for compatibility with older versions
    reloader: bool | None = None,
    # Unused parameters that we want to keep for compatibility but not actually use
    cdn_skulpt: str | None = None,
    cdn_skulpt_std: str | None = None,
    cdn_skulpt_drafter: str | None = None,
    # Custom overrides
    skip: bool | None = None,
    argv: list[str] | None = None,
    **extra_configuration,
) -> None:
    """Start the Drafter server (web or local development mode).

    Routes to either ClientServer (web mode) or AppServer (local dev mode)
    based on execution context. In web mode, initializes browser-side bridge;
    in local mode, starts Starlette dev server with file watching.

    This function is the primary entry point for users and accepts parameters
    for both ClientServer and AppServer modes (the appropriate ones are used
    depending on context).

    Args:
        initial_state: Optional initial application state.
        server: Optional pre-created server instance (defaults to main server).
        server_name: Server identifier name.
        in_debug_mode: Enable debug panel and logging.
        framed: Whether to frame the content.
        theme: Theme name (e.g., "default").
        site_title: Title displayed in UI.
        favicon: Browser tab icon: a URL or the path to an adjacent image
            file (svg, png, ico, ...).
        information: Dict of site information (author, description, etc.).
        verbose: Enable verbose logging.
        asset_directory: Assets directory (uses Drafter defaults if False).
        show_filename_as: Display filename in UI (if different from actual).
        engine: Python engine ("skulpt" or "pyodide").
        port: Server port for dev mode.
        host: Server host for dev mode.
        prerender_initial_page: Prerender initial page on startup.
        open_browser: Auto-open browser in dev mode.
        browser: Which browser to open in dev mode: "chrome", "firefox",
            "safari", "edge", or "default" for the system default. When not
            given, Chrome is used if installed, then Firefox, then the
            system default.
        inline_py: Inline code in HTML vs. load via HTTP.
        use_reloader: Enable file watcher and auto-reload.
        pyodide_url: Base URL to load Pyodide from (default: jsDelivr CDN).
        pyodide_version: Pyodide version segment, e.g. "v314.0.5" or "dev".
        pyodide_branch: Pyodide distribution branch, "full" or "debug".
        reloader: Deprecated alias for `use_reloader`, kept for
            compatibility with older versions; used only when
            `use_reloader` is not given.
        cdn_skulpt: Deprecated and ignored; passing a value prints a
            warning.
        cdn_skulpt_std: Deprecated and ignored; passing a value prints a
            warning.
        cdn_skulpt_drafter: Deprecated and ignored; passing a value
            prints a warning.
        skip: If True, do nothing at all — do not start the server or
            compile anything. Useful for running unit tests against a
            site file. Also settable via the DRAFTER_SKIP environment
            variable, the --skip flag, or a config file.
        argv: Command-line argument override passed into the system
            configuration.
        **extra_configuration: Additional configuration parameters.

    Raises:
        SystemExit: In local development mode, when the server cannot start
            for a reason that has a student-facing explanation (the main
            file is missing, the port is in use). The explanation is
            printed instead of a traceback; with the verbose setting on,
            the original `StudentFacingError` propagates instead.
    """
    # Handle compatibility for old parameters
    parameters: dict[str, Any] = {}
    if server_name is not None:
        parameters["server_name"] = server_name
    if in_debug_mode is not None:
        parameters["in_debug_mode"] = in_debug_mode
    if framed is not None:
        parameters["framed"] = framed
    if theme is not None:
        parameters["theme"] = theme
    if site_title is not None:
        parameters["site_title"] = site_title
    if favicon is not None:
        parameters["favicon"] = favicon
    if information is not None:
        parameters["information"] = information
    if verbose is not None:
        parameters["verbose"] = verbose
    if asset_directory is not None:
        parameters["asset_directory"] = asset_directory
    if show_filename_as is not None:
        parameters["show_filename_as"] = show_filename_as
    if engine is not None:
        parameters["engine"] = engine
    if port is not None:
        parameters["port"] = port
    if host is not None:
        parameters["host"] = host
    if prerender_initial_page is not None:
        parameters["prerender_initial_page"] = prerender_initial_page
    if open_browser is not None:
        parameters["open_browser"] = open_browser
    if browser is not None:
        parameters["browser"] = browser
    if inline_py is not None:
        parameters["inline_py"] = inline_py
    if reloader is not None and use_reloader is None:
        parameters["use_reloader"] = reloader
    elif use_reloader is not None:
        parameters["use_reloader"] = use_reloader
    if pyodide_url is not None:
        parameters["pyodide_url"] = pyodide_url
    if pyodide_version is not None:
        parameters["pyodide_version"] = pyodide_version
    if pyodide_branch is not None:
        parameters["pyodide_branch"] = pyodide_branch
    # Handle deprecated parameters that are no longer used but we want to keep for compatibility
    if cdn_skulpt is not None:
        print("Warning: 'cdn_skulpt' parameter is no longer used and will be ignored.")
    if cdn_skulpt_std is not None:
        print(
            "Warning: 'cdn_skulpt_std' parameter is no longer used and will be ignored."
        )
    if cdn_skulpt_drafter is not None:
        print(
            "Warning: 'cdn_skulpt_drafter' parameter is no longer used and will be ignored."
        )
    # Custom overrides
    if skip is not None:
        parameters["skip"] = skip
    if argv is not None:
        parameters["argv"] = argv
    parameters.update(extra_configuration)

    system = get_system_configuration()
    system.merge_in_args(parameters)

    # DRAFTER_SKIP / --skip / skip=True: do nothing, so the site file can be
    # imported (e.g., by unit tests) without starting a server or compiling.
    if system.bootstrap.skip:
        if system.bootstrap.verbose:
            print("Skipping server startup because the skip setting is enabled.")
        return

    server = server or get_main_server()

    setting_names = system.setting_names()
    report_unknown_options(
        find_unknown_options(extra_configuration, setting_names),
        setting_names,
        server,
    )
    caller = sys._getframe(1)
    report_code_after_start(server, caller.f_code.co_filename, caller.f_lineno)

    # Primary dispatch based on execution context
    if is_web():
        from drafter.bridge import run_client_bridge

        run_client_bridge(system, server, initial_state)
    elif system.bootstrap.mode == "compile_site":
        from drafter.builder.build import compile_site

        compile_site(system, server, initial_state)
    else:
        from drafter.app.app_server import serve_app_once

        try:
            serve_app_once(system, server, initial_state)
        except StudentFacingError as error:
            # There is no browser error page yet on the host, so present the
            # explanation in the terminal instead of a traceback (which the
            # verbose setting restores for debugging).
            if system.bootstrap.verbose:
                raise
            print(format_student_facing_error(error), file=sys.stderr)
            raise SystemExit(1) from None
