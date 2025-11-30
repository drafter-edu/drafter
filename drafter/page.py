from dataclasses import dataclass
from typing import Any, Union, List

from drafter.configuration import ServerConfiguration
from drafter.constants import RESTORABLE_STATE_KEY
from drafter.components import PageContent, Link


@dataclass
class Page:
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
    """
    state: Any
    content: list

    def __init__(self, state, content=None):
        if content is None:
            state, content = None, state
        self.state = state
        self.content = content

        if isinstance(content, (str, PageContent)):
            # If the content is a single string, convert it to a list with that string as the only element.
            self.content = [content]
        elif not isinstance(content, list):
            incorrect_type = type(content).__name__
            raise ValueError("The content of a page must be a list of strings or components."
                             f" Found {incorrect_type} instead.")
        else:
            for index, chunk in enumerate(content):
                if not isinstance(chunk, (str, PageContent)):
                    incorrect_type = type(chunk).__name__
                    raise ValueError("The content of a page must be a list of strings or components."
                                     f" Found {incorrect_type} at index {index} instead.")

    def render_content(self, current_state, configuration: ServerConfiguration) -> str:
        """
        Renders the content of the page to HTML. This will include the state of the page, if it is restorable.
        Users should not call this method directly; it will be called on their behalf by the server.

        :param current_state: The current state of the server. This will be used to restore the page if needed.
        :param configuration: The configuration of the server. This will be used to determine how the page is rendered.
        :return: A string of HTML representing the content of the page.
        """
        # TODO: Decide if we want to dump state on the page
        chunked = [
            # f'<input type="hidden" name="{RESTORABLE_STATE_KEY}" value={current_state!r}/>'
        ]
        for chunk in self.content:
            if isinstance(chunk, str):
                chunked.append(f"<p>{chunk}</p>")
            else:
                chunked.append(chunk.render(current_state, configuration))
        content = "\n".join(chunked)
        content = f"<form method='POST' enctype='multipart/form-data' accept-charset='utf-8'>{content}</form>"
        if configuration.framed:
            reset_button = self.make_reset_button()
            about_button = self.make_about_button()
            content = (f"<div class='container btlw-header'>{configuration.title}{reset_button}{about_button}</div>"
                       f"<div class='container btlw-container'>{content}</div>")
        return content

    def make_reset_button(self) -> str:
        """
        Creates a reset button that has the "reset" icon and title text that says "Resets the page to its original state.".
        Simply links to the "--reset" URL.

        :return: A string of HTML representing the reset button.
        """
        return '''<a href="--reset" class="btlw-reset" 
                    title="Resets the page to its original state. Any data entered will be lost."
                    onclick="return confirm('This will reset the page to its original state. Any data entered will be lost. Are you sure you want to continue?');"
                    >⟳</a>'''

    def make_about_button(self) -> str:
        """
        Creates an about button that has the "info" icon and title text that says "About Drafter.".
        Simply links to the "--about" URL.

        :return: A string of HTML representing the about button.
        """
        return '''<a href="--about" class="btlw-about" 
                    title="More information about this website"
                    >?</a>'''

    def verify_content(self, server) -> bool:
        """
        Verifies that the content of the page is valid. This will check that all links are valid and that
        all components are valid.
        This is not meant to be called by the user; it will be called by the server.

        :param server: The server to verify the content against.
        :return: True if the content is valid, False otherwise.
        """
        for chunk in self.content:
            if isinstance(chunk, Link):
                chunk.verify(server)
        return True


@dataclass
class Update:
    """
    An Update response is used when you want to update the state without changing the HTML content of the page.
    This is useful for background updates, form submissions that don't need visual feedback, or other scenarios
    where you want to modify the application state without re-rendering the entire page.

    When a function returns an Update object, the server will:
    1. Update the internal state to the new state value
    2. Send a minimal response to the client indicating success
    3. Not re-render or replace any HTML content

    :param state: The new state value to be stored on the server. This can be any type (dataclass, dict, list, etc.)
    """
    state: Any

    def __init__(self, state):
        self.state = state


@dataclass
class Fragment:
    """
    A Fragment response is used when you want to update a specific element on the page without re-rendering
    the entire page. This provides a more efficient way to update portions of the UI in response to events.

    When a function returns a Fragment object, the server will:
    1. Update the internal state to the new state value
    2. Render only the content specified in the Fragment
    3. Send instructions to the client to replace the target element's innerHTML with the new content

    The target parameter should be a CSS selector that identifies the element to update. Common selectors include:
    - "#element-id" for elements with a specific id attribute
    - ".class-name" for elements with a specific class
    - "[data-target='name']" for elements with a specific data attribute

    :param state: The new state value to be stored on the server
    :param target: A CSS selector string identifying which element to update
    :param content: A list of strings and/or PageContent components to render into the target element
    """
    state: Any
    target: str
    content: Union[List[Union[str, PageContent]], str, PageContent]

    def __init__(self, state, target: str, content):
        self.state = state
        self.target = target
        # Normalize content to always be a list
        if isinstance(content, (str, PageContent)):
            self.content = [content]
        elif not isinstance(content, list):
            incorrect_type = type(content).__name__
            raise ValueError("The content of a Fragment must be a string, PageContent, or a list of strings/components."
                             f" Found {incorrect_type} instead.")
        else:
            for index, chunk in enumerate(content):
                if not isinstance(chunk, (str, PageContent)):
                    incorrect_type = type(chunk).__name__
                    raise ValueError("The content of a Fragment must be a list of strings or components."
                                     f" Found {incorrect_type} at index {index} instead.")
            self.content = content

    def render_content(self, current_state, configuration: ServerConfiguration) -> str:
        """
        Renders the content of the Fragment to HTML.

        :param current_state: The current state of the server
        :param configuration: The configuration of the server
        :return: A string of HTML representing the content
        """
        chunked = []
        for chunk in self.content:
            if isinstance(chunk, str):
                chunked.append(f"<p>{chunk}</p>")
            else:
                chunked.append(chunk.render(current_state, configuration))
        return "\n".join(chunked)
