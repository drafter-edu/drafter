"""
Default error route, rendering a student-friendly error page.

Presents a plain-language summary and fix suggestions, plus technical
details including a traceback parsed into styled frames that highlight
which lines come from the student's own code.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from drafter.client_server.client_server import ClientServer
from drafter.payloads.kinds.page import Page
from drafter.components import (
    Header,
    Paragraph,
    PreformattedText,
    Span,
    BulletedList,
    Link,
    InlineCode,
    Div,
)
from drafter.data.errors import ErrorDetails

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
    function: Optional[str]
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


def _render_traceback(traceback_text: Optional[str]):
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


def _build_friendly_summary(error: ErrorDetails) -> str:
    """Return a plain-language summary of the failure for novice users."""
    if error.id == "request.route_not_found":
        return "Drafter could not find the page route your app tried to open."
    if error.category == "request":
        return "Drafter had trouble loading a page (route) from your app."
    if error.category == "payload":
        return "Drafter could not turn your page result into something it can display."
    if error.category == "runtime":
        return "Your Python code ran into an error while it was executing."
    if error.category == "config":
        return "Drafter found a configuration setting that it could not use."
    if error.category == "bridge":
        return "Drafter had trouble syncing your Python code with the browser."
    return "Your program hit an error and stopped this request before it could finish."


def _build_fix_steps(error: ErrorDetails) -> list[str]:
    """Build concrete next-step suggestions based on common error patterns."""
    combined = "\n".join(
        text for text in (error.message, error.details, error.traceback or "") if text
    )

    if error.id == "request.route_not_found":
        return [
            "Check route names and links so they match exactly (including dashes and slashes).",
            "Confirm that the route is added before your app starts handling requests.",
            "Use the 'Return to Index Page' link below to get back to a known page.",
        ]

    if "SyntaxError" in combined:
        return [
            "Go to the file and line number shown in the traceback.",
            "Check for missing colons, commas, quotes, or parentheses on that line.",
            "Run again after fixing one syntax problem at a time.",
        ]

    if "NameError" in combined:
        return [
            "Look for a misspelled variable or function name.",
            "Make sure the variable is created before you use it.",
            "Check capitalization because Python names are case-sensitive.",
        ]

    if "TypeError" in combined:
        return [
            "Check that each function call has the right number of arguments.",
            "Verify that values have the type your code expects (for example, text vs number).",
            "Print intermediate values to see what type they are before the failing line.",
        ]

    if "IndexError" in combined or "KeyError" in combined:
        return [
            "Check that the list index or dictionary key exists before using it.",
            "Print the list length or dictionary keys right before the failing line.",
            "Add a guard condition so missing data is handled safely.",
        ]

    return [
        "Read the technical message below and locate the first relevant line in the traceback.",
        "Fix that first error, then run again and see if any new message appears.",
        "If you are stuck, share the error ID and traceback with your instructor or teammate.",
    ]


def default_error(state, error: ErrorDetails, server: ClientServer):
    """Default error route handler.

    Args:
        state: Current application state.
        error: The error that occurred.
        server: The ClientServer instance, used to include debug information
            when enabled.

    Returns:
        Page content with error information.
    """
    friendly_summary = _build_friendly_summary(error)
    fix_steps = _build_fix_steps(error)
    content = [
        Div(
            Header("Something Went Wrong", level=2),
            Paragraph(friendly_summary),
            Header("What To Try Next", level=3),
            BulletedList(fix_steps),
            Header("Technical Details", level=3),
            Paragraph("Error ID:", InlineCode(error.id)),
            Paragraph("Message:"),
            PreformattedText(error.message),
            Paragraph("Status:", InlineCode(error.status_code or "error")),
            Paragraph("Severity:", InlineCode(error.severity)),
            Paragraph(
                "Recoverable:",
                InlineCode("yes" if error.recoverable else "no"),
            ),
            Paragraph("Traceback:"),
            _render_traceback(error.traceback),
            Paragraph("Details:"),
            PreformattedText(error.details),
            Paragraph("Category:", InlineCode(error.category)),
            Paragraph("Navigation options:"),
            BulletedList(
                [
                    Link("Return to Index Page", "index"),
                    Link("Reset State and Return to Index", "--reset"),
                    Link("Reload Page", "--reload"),
                ]
            ),
            classes="error-page",
        ),
    ]
    # TODO: Consider a hard refresh option that appends a nonce to the URL
    return Page(state, content)
