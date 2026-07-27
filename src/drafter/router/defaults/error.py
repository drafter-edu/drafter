"""
Default error route, rendering a student-friendly error page.

Presents a plain-language summary and fix suggestions, plus technical
details including a traceback parsed into styled frames that highlight
which lines come from the student's own code.
"""

import re
from dataclasses import dataclass, field

from drafter.client_server.client_server import ClientServer
from drafter.components import (
    BulletedList,
    Details,
    Div,
    Header,
    InlineCode,
    Link,
    Paragraph,
    PreformattedText,
    Span,
    Table,
)
from drafter.data.error_explainer import explain
from drafter.data.errors import ErrorDetails
from drafter.payloads.kinds.page import Page

#: Matches CPython frame lines like: File "main.py", line 6, in index
_TRACEBACK_FRAME_PATTERN = re.compile(
    r'^\s*File "(?P<filename>[^"]+)", line (?P<line>\d+)(?:, in (?P<function>.+))?\s*$'
)

#: Path fragments that indicate a frame is internal (Drafter or the runtime),
#: rather than the student's own code.
_INTERNAL_PATH_MARKERS = (
    "drafter",
    "site-packages",
    "/lib/python",
    "\\lib\\python",
    "importlib",
    "pyodide",
)


@dataclass
class _TracebackFrame:
    """One stack frame parsed out of a traceback."""

    filename: str
    line_number: str
    function: str | None
    code_lines: list[str] = field(default_factory=list)

    @property
    def is_student_code(self) -> bool:
        lowered = self.filename.lower()
        if lowered.startswith("<"):
            return False
        return not any(marker in lowered for marker in _INTERNAL_PATH_MARKERS)


def _parse_traceback(
    traceback_text: str,
) -> tuple[list[str], list[_TracebackFrame], list[str]]:
    """Split traceback text into header lines, stack frames, and the final error.

    Returns:
        Tuple of (header_lines, frames, exception_lines). If no frames were
        recognized, frames is empty and callers should fall back to plain text.
    """
    header_lines: list[str] = []
    frames: list[_TracebackFrame] = []
    exception_lines: list[str] = []

    for line in traceback_text.splitlines():
        match = _TRACEBACK_FRAME_PATTERN.match(line)
        if match:
            frames.append(
                _TracebackFrame(
                    filename=match.group("filename"),
                    line_number=match.group("line"),
                    function=match.group("function"),
                )
            )
        elif not frames:
            if line.strip():
                header_lines.append(line.strip())
        elif line.startswith((" ", "\t")):
            # Indented lines belong to the most recent frame (source + carets).
            frames[-1].code_lines.append(line)
        elif line.strip():
            # Unindented lines after frames are the exception message itself.
            exception_lines.append(line.rstrip())

    return header_lines, frames, exception_lines


def _render_traceback_frame(frame: _TracebackFrame):
    """Render a single stack frame as a styled block."""
    location_parts = [
        Span("File ", classes="traceback-label"),
        InlineCode(frame.filename),
        Span(", line ", classes="traceback-label"),
        InlineCode(frame.line_number),
    ]
    if frame.function:
        location_parts.append(Span(", in ", classes="traceback-label"))
        location_parts.append(InlineCode(frame.function))
    if frame.is_student_code:
        location_parts.append(Span("your code", classes="traceback-badge"))

    children: list = [Div(*location_parts, classes="traceback-location")]
    if frame.code_lines:
        # Dedent uniformly so the code and any caret markers stay aligned.
        indent = min(len(line) - len(line.lstrip()) for line in frame.code_lines)
        code_text = "\n".join(line[indent:] for line in frame.code_lines)
        children.append(PreformattedText(code_text, classes="traceback-code"))

    frame_classes = "traceback-frame" + (
        " is-student-code" if frame.is_student_code else ""
    )
    return Div(*children, classes=frame_classes)


#: Lines that join chained tracebacks together (exception during exception).
_CHAIN_MARKERS = (
    "During handling of the above exception, another exception occurred:",
    "The above exception was the direct cause of the following exception:",
)


def _split_chained_tracebacks(traceback_text: str) -> list[str]:
    """Split chained tracebacks into their individual sections.

    The chain marker lines are kept as the first line of the section they
    introduce so the reader still sees how the parts relate.
    """
    sections: list[list[str]] = [[]]
    for line in traceback_text.splitlines():
        if line.strip() in _CHAIN_MARKERS:
            sections.append([line.strip()])
        else:
            sections[-1].append(line)
    return [
        "\n".join(section) for section in sections if any(s.strip() for s in section)
    ]


def _render_traceback_section(section_text: str) -> list:
    """Render one (unchained) traceback section as a list of components."""
    header_lines, frames, exception_lines = _parse_traceback(section_text)
    if not frames:
        return [PreformattedText(section_text)]

    children: list = []
    if header_lines:
        children.append(Div(*header_lines, classes="traceback-header"))
    children.extend(_render_traceback_frame(frame) for frame in frames)
    if exception_lines:
        children.append(
            PreformattedText("\n".join(exception_lines), classes="traceback-exception")
        )
    return children


def _render_traceback(traceback_text: str | None):
    """Render a traceback as structured, styled blocks.

    Falls back to plain preformatted text when there is no traceback or the
    text does not look like a standard Python traceback.
    """
    if not traceback_text or not traceback_text.strip():
        return PreformattedText("No traceback available.")

    _, frames, _ = _parse_traceback(traceback_text)
    if not frames:
        return PreformattedText(traceback_text)

    children = [
        Paragraph(
            "Read from the bottom up: the last line names the error, and the "
            "nearest \u201cyour code\u201d entry above it shows where to look.",
            classes="traceback-hint",
        )
    ]
    for section in _split_chained_tracebacks(traceback_text):
        children.extend(_render_traceback_section(section))
    return Div(*children, classes="drafter-traceback")


def _render_step(text: str):
    """Render one "what to try next" step, honoring backtick code marks.

    Step strings may wrap code fragments in backticks (like `` `this` ``);
    those fragments become inline code. Steps without backticks pass
    through as plain strings.
    """
    if "`" not in text:
        return text
    parts: list = []
    for index, segment in enumerate(text.split("`")):
        if not segment:
            continue
        # Odd split positions are inside backticks.
        parts.append(InlineCode(segment) if index % 2 == 1 else segment)
    return Span(*parts)


def _render_data_value(value):
    """Render one JSON-safe structured-data value as nested components.

    Dictionaries become nested key/value tables, lists become bulleted
    lists, and scalars become inline code (or a preformatted block for
    long/multi-line text), so arbitrarily nested envelope `data` reads as
    structure instead of one long repr string.
    """
    if isinstance(value, dict):
        if not value:
            return InlineCode("{}")
        return Table(
            [
                [Span(str(key), classes="error-data-key"), _render_data_value(item)]
                for key, item in value.items()
            ],
            classes="error-data-table",
        )
    if isinstance(value, (list, tuple)):
        if not value:
            return InlineCode("[]")
        return BulletedList([_render_data_value(item) for item in value])
    if value is None or isinstance(value, (bool, int, float)):
        return InlineCode(repr(value))
    text = str(value)
    if "\n" in text or len(text) > 80:
        return PreformattedText(text)
    return InlineCode(text)


def _render_route_call(error: ErrorDetails):
    """Render the generated route call, noting when it is approximate."""
    call = PreformattedText(str(error.data["route_call"]), classes="error-route-call")
    if error.data.get("route_call_exact", False):
        return call
    return Div(
        call,
        Paragraph(
            "(approximate — built from the raw request values, since the "
            "arguments were never fully matched to the route)",
            classes="error-route-call-note",
        ),
    )


def _build_technical_rows(error: ErrorDetails) -> list:
    """Build the rows of the technical-details table for an envelope."""
    data = error.data if isinstance(error.data, dict) else {}
    rows: list = [
        ["Error ID", InlineCode(error.id)],
        ["Message", PreformattedText(error.message)],
    ]
    if data.get("route_call"):
        rows.append(["Route Call", _render_route_call(error)])
    rows.extend(
        [
            ["Status", InlineCode(error.status_code or "error")],
            ["Severity", InlineCode(error.severity)],
            ["Category", InlineCode(error.category)],
            ["Recoverable", InlineCode("yes" if error.recoverable else "no")],
        ]
    )
    for key, value in data.items():
        if key in ("route_call", "route_call_exact"):
            continue
        rendered = _render_data_value(value)
        if isinstance(value, (dict, list, tuple)) and value:
            # Nested structures (like the full request) start collapsed so
            # the table stays scannable; one click expands them.
            rendered = Details(
                Span("Show details", classes="error-data-summary"),
                rendered,
                open=False,
            )
        rows.append([key.replace("_", " ").title(), rendered])
    if error.details:
        rows.append(["Details", PreformattedText(error.details)])
    rows.append(["Traceback", _render_traceback(error.traceback)])
    return rows


def default_error(state, error: ErrorDetails, server: ClientServer):
    """Default error route handler.

    Args:
        state: Current application state.
        error: The error that occurred.
        server: The ClientServer instance, used to include debug information
            when enabled.

    Returns:
        Page content with error information.

    The error page content can be customized via configuration:
    `error_page_title` replaces the heading, `error_page_message` replaces
    the friendly summary, and `error_page_show_details=False` hides the
    technical details/traceback section (useful on deployed sites).
    """
    configuration = server.get_current_configuration()
    # The envelope normally arrives with its friendly tier already filled in
    # by the producer; explain() returns those fields untouched (the envelope
    # is itself an exception carrying them) and only derives fallback text
    # for envelopes from producers that did not provide any. Configuration
    # overrides always win over the derived title/summary.
    explanation = explain(error, error.id, error.category)
    title = getattr(configuration, "error_page_title", "") or explanation.title
    friendly_summary = (
        getattr(configuration, "error_page_message", "") or explanation.message
    )
    show_details = getattr(configuration, "error_page_show_details", True)
    sections: list = [
        Header(title, level=2),
        Paragraph(friendly_summary),
        PreformattedText(f"{error.id}: {error.message}"),
        Header("What To Try Next", level=3),
        BulletedList([_render_step(step) for step in explanation.steps]),
        Header("Navigation Options:", level=3),
        BulletedList(
            [
                Link("Return to Index Page", "index"),
                Link("Reset State and Return to Index", "--reset"),
                Link("Reload Entire Application", "--reload"),
                Link("Submit a Bug Report", "--bug-report"),
            ]
        ),
    ]

    if show_details:
        sections.extend(
            [
                Header("Technical Details", level=3),
                Table(_build_technical_rows(error)),
            ]
        )
    content = [Div(*sections, classes="error-page")]
    # TODO: Consider a hard refresh option that appends a nonce to the URL
    return Page(state, content)
