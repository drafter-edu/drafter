"""Default "--bug-report" route, explaining when and how to report a bug.

The page clarifies that bug reports are for actual defects or limitations in
Drafter itself (not for getting help with an assignment) and offers a button
that downloads the same bug-report bundle as the debug panel's Help menu
(telemetry events, system status, page context).
"""

from dataclasses import dataclass

from drafter.client_server.client_server import ClientServer
from drafter.components import (
    BulletedList,
    Button,
    Header,
    Paragraph,
)
from drafter.components.page_content import Component, ComponentArgument, PageContent
from drafter.payloads.kinds.page import Page
from drafter.site.site import DRAFTER_TAG_IDS


@dataclass(repr=False)
class DownloadBugReportButton(Component):
    """Button that downloads the bug-report bundle when clicked.

    Rendered with the well-known ``BUG_REPORT_DOWNLOAD`` element id; after
    each page commit the client bridge attaches a click listener to that id
    (see ``EventManager.mount_bug_report_download``) which asks the debug
    panel for the same bundle as the Help menu's "Download Bug Report" item.
    ``type="button"`` keeps the click from submitting the surrounding site
    form, and the button carries no ``data-nav``, so the bridge's navigation
    delegation ignores it.
    """

    text: PageContent
    tag = "button"

    DEFAULT_ATTRS = {"type": "button"}
    KNOWN_ATTRS = ["type", "disabled"]
    ARGUMENTS = [ComponentArgument("text", is_content=True)]

    def __init__(self, text: PageContent = "Download Bug Report", **extra_settings):
        """Initialize the download button.

        Args:
            text: The button's label.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.text = text
        extra_settings.setdefault("id", DRAFTER_TAG_IDS["BUG_REPORT_DOWNLOAD"])
        self.extra_settings = extra_settings


def default_bug_report(state, _server: ClientServer):
    """Generate the page shown for the ``--bug-report`` system route.

    Explains when filing a bug report is appropriate (an actual bug or
    limitation in Drafter itself) and when it is not (getting help with an
    assignment), and provides a button that downloads the bug-report bundle
    used to diagnose problems.

    Args:
        state: Current application state, passed through to the returned Page.
        _server: The running ClientServer; the underscore prefix marks this as
            a framework-injected parameter, so it is supplied automatically
            rather than from the request payload.

    Returns:
        Page: The bug-report information page.
    """
    return Page(
        state,
        [
            Header("Submit a Bug Report", level=1),
            Paragraph(
                "Bug reports are how the Drafter developers learn about "
                "problems in Drafter itself. Before you send one, make sure "
                "a bug report is actually the right tool."
            ),
            Header("When a bug report is appropriate", level=2),
            BulletedList(
                [
                    "Drafter crashed, froze, or displayed something incorrectly "
                    "even though your code looks correct.",
                    "Drafter behaved differently than its documentation says it should.",
                    "You ran into a limitation of Drafter that stopped you from "
                    "building something reasonable.",
                    "An error message from Drafter was wrong, confusing, or unhelpful.",
                ]
            ),
            Header("When a bug report is NOT appropriate", level=2),
            Paragraph(
                "A bug report is not a way to get help with your homework or "
                "your own code. The developers cannot debug your assignment "
                "for you."
            ),
            BulletedList(
                [
                    "Your own code has an error: read the error page and the "
                    "traceback, and use the debug panel to investigate.",
                    "You are not sure how to build something: check the Drafter "
                    "documentation and examples first.",
                    "You need help with an assignment: ask your instructor, "
                    "teaching assistant, or classmates.",
                ]
            ),
            Header("How to submit a bug report", level=2),
            Paragraph(
                "The button below downloads a file of debugging details: your "
                "code, recent activity, any errors, and information about your "
                "browser and environment. Review it before sharing if it might "
                "contain anything personal."
            ),
            DownloadBugReportButton(),
            Paragraph(
                "Email it to your Dr. Bart (acbart@udel.edu). "
                "Describe what you were doing, what you expected to "
                "happen, and what happened instead.",
            ),
            Button("Back to Index (Main Page)", "index"),
        ],
    )
