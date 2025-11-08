from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from drafter.data.channel import Message
from drafter.config.client_server import ClientServerConfiguration
from drafter.configuration import ServerConfiguration
from drafter.constants import RESTORABLE_STATE_KEY
from drafter.components import Component, PageContent, Link
from drafter.data.request import Request
from drafter.history.state import SiteState
from drafter.payloads.payloads import ResponsePayload
from drafter.payloads.failure import VerificationFailure
from drafter.router.routes import Router


@dataclass
class Page(ResponsePayload):
    """
    A page is a collection of content to be displayed to the user. This content has two critical parts:

    - The ``state``, which is the current value of the backend server for this user's session. This is used to
      restore the state of the page when the user navigates back to it. Typically, this will be a dataclass
      or a dictionary, but could also be a list, primitive value, or even None.
    - The ``content``, which is a list of strings and components that will be rendered to the user.

    The content of a page can be any combination of strings and components. Strings will be rendered as paragraphs,
    while components will be rendered as their respective HTML. Components should be classes that inherit from
    ``drafter.components.PageContent``. If the content is not a list, a ValueError will be raised.

    :param state: The state of the page. If only one argument is provided, this will default to be ``None``.
    :param content: The content of the page. Must always be provided as a list of strings and components.
    :param css: Optional CSS content to inject dynamically when this page is rendered.
    :param js: Optional JavaScript content to inject dynamically when this page is rendered.
    """

    state: Any
    content: list
    css: List[str] = field(default_factory=list)
    js: List[str] = field(default_factory=list)

    def __init__(self, state, content=None, css=None, js=None):
        if content is None:
            state, content = None, state
        self.state = state
        self.content = content
        self.css = css if css is not None else []
        self.js = js if js is not None else []

        if isinstance(content, (str, Component)):
            # If the content is a single string, convert it to a list with that string as the only element.
            self.content = [content]
        elif not isinstance(content, list):
            incorrect_type = type(content).__name__
            raise ValueError(
                "The content of a page must be a list of strings or components."
                f" Found {incorrect_type} instead."
            )
        else:
            for index, chunk in enumerate(content):
                if not isinstance(chunk, (str, Component)):
                    incorrect_type = type(chunk).__name__
                    raise ValueError(
                        "The content of a page must be a list of strings or components."
                        f" Found {incorrect_type} at index {index} instead."
                    )

    def get_state_updates(self) -> tuple[bool, Any]:
        return True, self.state

    def render(
        self, state: SiteState, configuration: ClientServerConfiguration
    ) -> Optional[str]:
        """
        Renders the content of the page to HTML. This will include the state of the page, if it is restorable.
        Users should not call this method directly; it will be called on their behalf by the server.

        :param current_state: The current state of the server. This will be used to restore the page if needed.
        :param configuration: The configuration of the server. This will be used to determine how the page is rendered.
        :return: A string of HTML representing the content of the page.
        """
        # TODO: Decide if we want to dump state on the page
        chunked: list[str] = [
            # f'<input type="hidden" name="{RESTORABLE_STATE_KEY}" value={current_state!r}/>'
        ]
        for chunk in self.content:
            if isinstance(chunk, str):
                chunked.append(f"<p>{chunk}</p>")
            else:
                chunked.append(chunk.render(state, configuration))
        content = "\n".join(chunked)
        content = f"<div id='drafter-page--'>{content}</div>"
        content = f"<form id='drafter-form--' enctype='multipart/form-data' accept-charset='utf-8'>{content}</form>"
        # TODO: Introduce a new parent that can handle debug mode rendering
        if configuration.in_debug_mode:
            reset_button = self.make_reset_button()
            about_button = self.make_about_button()
            content = (
                f"<div class='container' id='drafter-debug-header--'>{configuration.site_title}{reset_button}{about_button}</div>"
                f"<div class='container' id='drafter-app--'>{content}</div>"
            )
        return content

    def get_messages(
        self,
        state: SiteState,
        configuration: ClientServerConfiguration,
    ) -> list[Message]:
        # Add CSS as style messages in the "before" channel
        messages = []
        for css_content in self.css:
            messages.append(
                Message(
                    channel_name="before",
                    kind="style",
                    sigil=None,
                    content=css_content,
                )
            )

        # Add JS as script messages in the "after" channel
        for js_content in self.js:
            messages.append(
                Message(
                    channel_name="after",
                    kind="script",
                    sigil=None,
                    content=js_content,
                )
            )
        return messages

    def make_reset_button(self) -> str:
        """
        Creates a reset button that has the "reset" icon and title text that says "Resets the page to its original state.".
        Simply links to the "--reset" URL.

        :return: A string of HTML representing the reset button.
        """
        return """<a href="--reset" class="btlw-reset" 
                    title="Resets the page to its original state. Any data entered will be lost."
                    onclick="return confirm('This will reset the page to its original state. Any data entered will be lost. Are you sure you want to continue?');"
                    >⟳</a>"""

    def make_about_button(self) -> str:
        """
        Creates an about button that has the "info" icon and title text that says "About Drafter.".
        Simply links to the "--about" URL.

        :return: A string of HTML representing the about button.
        """
        return """<a href="--about" class="btlw-about" 
                    title="More information about this website"
                    >?</a>"""

    def verify(
        self,
        router: Router,
        state: SiteState,
        configuration: ClientServerConfiguration,
        request: Request,
    ) -> Optional[VerificationFailure]:
        """
        Verifies that the content of the page is valid. This will check that all links are valid and that
        all components are valid.
        This is not meant to be called by the user; it will be called by the server.

        :param server: The server to verify the content against.
        :return: True if the content is valid, False otherwise.
        """
        original_function = request.url
        if isinstance(self.content, str):
            return VerificationFailure(
                f"The server did not return a valid Page() object from {original_function}.\n"
                f"Instead of a list of strings or content objects, the content field was a string:\n"
                f" {self.content!r}\n"
                f"Make sure you return a Page object with the new state and the list of strings/content objects."
            )
        elif not isinstance(self.content, list):
            return VerificationFailure(
                f"The server did not return a valid Page() object from {original_function}.\n"
                f"Instead of a list of strings or content objects, the content field was:\n"
                f" {self.content!r}\n"
                f"Make sure you return a Page object with the new state and the list of strings/content objects."
            )
        else:
            for item in self.content:
                if not isinstance(item, (str, PageContent)):
                    return VerificationFailure(
                        f"The server did not return a valid Page() object from {original_function}.\n"
                        f"Instead of a list of strings or content objects, the content field was:\n"
                        f" {self.content!r}\n"
                        f"One of those items is not a string or a content object. Instead, it was:\n"
                        f" {item!r}\n"
                        f"Make sure you return a Page object with the new state and the list of strings/content objects."
                    )

        # Recursively verify each content chunk
        try:
            for chunk in self.content:
                chunk.verify(state, configuration, request)
        except Exception as e:
            return VerificationFailure(
                f"While verifying the Page() object returned from {original_function}, an error was encountered:\n"
                f"{e}"
            )
        return None
