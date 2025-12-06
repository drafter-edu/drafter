from dataclasses import dataclass
from typing import Any

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
    js: list

    def __init__(self, state, content=None, js=None):
        if content is None:
            state, content = None, state
        self.state = state
        self.content = content
        if isinstance(js, str):
            self.js = [js]
        elif js is None:
            self.js = []
        elif isinstance(js, list):
            for index, line in enumerate(js):
                if not isinstance(line, str):
                    incorrect_type = type(line).__name__
                    raise ValueError("The js parameter must be a string or a list of strings."
                                     f" Found {incorrect_type} at index {index} instead.")
            self.js = js
        else:
            raise ValueError("The js parameter must be a string or a list of strings.")

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


    def __repr__(self):
        if not self.js:
            return f"Page(state={self.state!r}, content={self.content!r})"
        return f"Page(state={self.state!r}, content={self.content!r}, js={self.js!r})"

    def render_content(self, current_state, configuration: ServerConfiguration) -> tuple[str, str]:
        """
        Renders the content of the page to HTML. This will include the state of the page, if it is restorable.
        Users should not call this method directly; it will be called on their behalf by the server.

        :param current_state: The current state of the server. This will be used to restore the page if needed.
        :param configuration: The configuration of the server. This will be used to determine how the page is rendered.
        :return: A string of HTML representing the content of the page.
        """
        # Check for duplicate form field names before rendering
        self._check_duplicate_form_names()
        
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

        js  = "\n".join([line if line.strip().startswith("<script") else f"<script>{line}</script>"
                         for line in self.js])

        return content, js

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

    def _check_duplicate_form_names(self):
        """
        Checks for duplicate form field names in the page content and issues warnings.
        
        This method examines all PageContent components in the page that have form names
        (excluding Button components which use --submit-button as their actual name)
        and warns if multiple components use the same name.
        """
        form_field_names = []
        
        for chunk in self.content:
            if isinstance(chunk, PageContent) and hasattr(chunk, 'name'):
                # Skip Button components as they don't actually use their 'name' parameter
                # as a form field name (they use --submit-button instead)
                from drafter.components import Button
                if not isinstance(chunk, Button):
                    form_field_names.append(chunk.name)
        
        # Find duplicates
        seen_names = set()
        duplicate_names = set()
        for name in form_field_names:
            if name in seen_names:
                duplicate_names.add(name)
            seen_names.add(name)
        
        # Issue warnings for duplicates
        if duplicate_names:
            import warnings
            duplicate_list = sorted(duplicate_names)
            if len(duplicate_list) == 1:
                warnings.warn(
                    f"Multiple form components use the same name '{duplicate_list[0]}'. "
                    f"This can cause unpredictable behavior when the form is submitted, "
                    f"as only one value may be received by the server. Consider using "
                    f"different names for each form component.",
                    UserWarning,
                    stacklevel=3
                )
            else:
                warnings.warn(
                    f"Multiple form components use the same names: {', '.join(repr(name) for name in duplicate_list)}. "
                    f"This can cause unpredictable behavior when the form is submitted, "
                    f"as only one value may be received by the server for each duplicate name. "
                    f"Consider using different names for each form component.",
                    UserWarning,
                    stacklevel=3
                )
