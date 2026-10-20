"""Default "--stop-server" route, which stops the local development server.

The page explains what stopping the server means and offers a button that
asks the development server to shut down. The button only does something
while the site is served by Drafter's local development server (and the
debug panel is available); on a deployed site there is no server to stop.
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
class StopServerButton(Component):
    """Button that stops the local development server when clicked.

    Rendered with the well-known ``STOP_SERVER`` element id; after each page
    commit the client bridge attaches a click listener to that id (see
    ``EventManager.mount_stop_server_button``) which asks the debug panel to
    send the stop request, the same action as the Navigate menu's "Stop
    Server" item but without a second confirmation, since this page is the
    confirmation. ``type="button"`` keeps the click from submitting the
    surrounding site form, and the button carries no ``data-nav``, so the
    bridge's navigation delegation ignores it.
    """

    text: PageContent
    tag = "button"

    DEFAULT_ATTRS = {"type": "button"}
    KNOWN_ATTRS = ["type", "disabled"]
    ARGUMENTS = [ComponentArgument("text", is_content=True)]

    def __init__(self, text: PageContent = "Yes, stop the server", **extra_settings):
        """Initialize the stop button.

        Args:
            text: The button's label.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.text = text
        extra_settings.setdefault("id", DRAFTER_TAG_IDS["STOP_SERVER"])
        self.extra_settings = extra_settings


def default_stop_server(state, _server: ClientServer):
    """Generate the page shown for the ``--stop-server`` system route.

    Explains that stopping the server ends the Drafter program running on
    the student's computer, what happens to the browser tab afterwards, and
    how to start again, then provides the button that sends the stop
    request. Visiting the page does nothing by itself; only the button
    stops the server.

    Args:
        state: Current application state, passed through to the returned Page.
        _server: The running ClientServer; the underscore prefix marks this as
            a framework-injected parameter, so it is supplied automatically
            rather than from the request payload.

    Returns:
        Page: The stop-server confirmation page.
    """
    return Page(
        state,
        [
            Header("Stop the Server?", level=1),
            Paragraph(
                "This stops Drafter's local development server: the Python "
                "program running in your terminal or editor that serves this "
                "site. Nothing happens until you click the button below."
            ),
            Header("What happens when you stop it", level=2),
            BulletedList(
                [
                    "Your program finishes, the same as pressing Ctrl+C in the terminal.",
                    "This browser tab stays open, but clicking around the site "
                    "will no longer work, and reloading the page will fail.",
                    "To start again, run your Python file again.",
                ]
            ),
            Paragraph(
                "If this site is deployed on the web rather than running from "
                "your own computer, there is no server to stop and the button "
                "will say so."
            ),
            StopServerButton(),
            Button("Back to Index (Main Page)", "index"),
        ],
    )
