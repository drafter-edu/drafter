"""The `Page` payload: a full-page response targeting the document body."""

from dataclasses import dataclass
from typing import Any

from drafter.components.page_content import PLAIN_CONTENT_TYPES
from drafter.config.client_server import ClientServerConfiguration
from drafter.data.errors import StudentFacingError, with_article
from drafter.data.request import Request
from drafter.history.formatting import format_page_content
from drafter.history.state import SiteState
from drafter.payloads.failure import VerificationFailure
from drafter.payloads.kinds.fragment import Fragment
from drafter.payloads.target import DEFAULT_BODY_TARGET
from drafter.payloads.verification import verify_unique_component_names
from drafter.router.routes import Router

_LONGEST_TEXT_IN_EXAMPLE = 30
"""Text longer than this is shortened when an error shows a corrected call."""


def _show_content_item(item: Any) -> str:
    """Write one piece of content the way it would appear in a `Page` call.

    Args:
        item: A piece of page content, or something mistaken for one.

    Returns:
        The `repr` of plain values (long text is shortened), and
        `Name(...)` for anything else.
    """
    if isinstance(item, str) and len(item) > _LONGEST_TEXT_IN_EXAMPLE:
        return repr(item[:_LONGEST_TEXT_IN_EXAMPLE] + "...")
    if isinstance(item, PLAIN_CONTENT_TYPES):
        return repr(item)
    return f"{type(item).__name__}(...)"


def _forgotten_brackets_error(
    content: Any, extra_content: tuple[Any, ...]
) -> StudentFacingError:
    """Build the error for values written after a `Page`'s content.

    `Page(state, "Hello", "there")` has two pieces of content and no list
    around them. The error shows the same call with the brackets added.

    Args:
        content: The value in the content position.
        extra_content: The unnamed values written after it.

    Returns:
        The error to raise.
    """
    items = content if isinstance(content, list) else [content]
    corrected = ", ".join(_show_content_item(item) for item in [*items, *extra_content])
    extras = ", ".join(with_article(type(item).__name__) for item in extra_content)
    return StudentFacingError(
        "The content of a Page must be given as one list, but more was "
        f"written after the content: {extras}.",
        title="Page Content Problem",
        friendly=(
            "A Page takes all of its content in one list. Something was "
            f"written after the content, outside the list: {extras}."
        ),
        steps=(
            "Put square brackets around all of the content, like "
            f"Page(state, [{corrected}]).",
            "If you meant to give the Page some CSS or JavaScript, name "
            "it, like css='...' or js='...'.",
        ),
    )


@dataclass
class Page(Fragment):
    """
    A page is a full-page response that replaces the entire body content.

    Page is a specialized Fragment that uses a default target pointing to the body element.
    This content has two critical parts:

    - The ``state``, which is the current value of the backend server for this user's session. This is used to
      restore the state of the page when the user navigates back to it. Typically, this will be a dataclass
      or a dictionary, but could also be a list, primitive value, or even None.
    - The ``content``, which is a list of strings, numbers, booleans, and components that will be rendered to the user.

    The content of a page can be any combination of strings, numbers, booleans, and components. Strings will be
    rendered as paragraphs, numbers and booleans will be rendered as their text form, and components will be rendered
    as their respective HTML. Components should be classes that inherit from
    ``drafter.components.PageContent``. A single string, number, boolean, or component is also accepted
    and treated as a list of one item; any other content raises a ``StudentFacingError`` (a ``ValueError``).

    Args:
        state: The state of the page. If only one argument is provided, this will default to be ``None``.
        content: The content of the page: a list of strings, numbers, booleans, and components.
        *extra_content: Not accepted. Anything written after the content
            is almost always content that was meant to go inside the
            list, so it raises an error that shows the corrected call.
        css: Optional CSS content to inject dynamically when this page is rendered.
            Must be given by name, as in ``css="..."``.
        js: Optional JavaScript content to inject dynamically when this page is rendered.
            Must be given by name, as in ``js="..."``.

    Raises:
        StudentFacingError: If anything is written after the content
            without a name, or if the content, ``css``, or ``js`` is not
            something a page can hold.

    Example:
        ```python
        Page(state, ["Hello!", Button("Next", "next")])
        ```
    """

    def __init__(self, state, content=None, *extra_content, css=None, js=None):
        if extra_content:
            raise _forgotten_brackets_error(content, extra_content)
        # Page always targets the body element
        super().__init__(state, content, target=DEFAULT_BODY_TARGET, css=css, js=js)

    def verify(
        self,
        router: Router,
        state: SiteState,
        configuration: ClientServerConfiguration,
        request: Request,
    ) -> VerificationFailure | None:
        """
        Verifies that the content of the page is valid. This will check that all links are valid and that
        all components are valid.
        This is not meant to be called by the user; it will be called by the server.

        Args:
            router: The server to verify the content against.
            state: The state of the server.
            configuration: The configuration of the server.
            request: The request being processed.

        Returns:
            None if the content is valid, a VerificationFailure otherwise.
        """
        original_function = request.url
        # The constructor always stores a list, so this only catches content
        # that was replaced after the Page was made.
        if not isinstance(self.content, list):
            return VerificationFailure(
                f"The server did not return a valid Page() object from {original_function}.\n"
                f"Instead of a list of strings or content objects, the content field was:\n"
                f" {self.content!r}\n"
                f"Make sure you return a Page object with the new state and the list of strings/content objects.",
                friendly_title="Page Content Problem",
                friendly_message=(
                    f"The Page returned from `{original_function}` has "
                    f"content that is {with_article(type(self.content).__name__)} "
                    "instead of a list."
                ),
                friendly_steps=(
                    "Make the content argument of Page a list, like "
                    "Page(state, ['Hello!']).",
                ),
            )
        else:
            from drafter.components.page_content import (
                validate_page_content,
            )

            for item in self.content:
                is_valid, error_message = validate_page_content(item)
                if not is_valid:
                    return VerificationFailure(
                        f"The server did not return a valid Page() object from {original_function}.\n"
                        f"Instead of a list of strings, numbers, booleans, or content objects, the content field was:\n"
                        f" {self.content!r}\n"
                        f"One of those items is not a string, number, boolean, or content object. Instead, it was:\n"
                        f" {item!r}\n"
                        f"Validation error: {error_message}\n"
                        f"Make sure you return a Page object with the new state and the list of strings/content objects.",
                        friendly_title="Page Content Problem",
                        friendly_message=(
                            f"One of the items in the content list of the "
                            f"Page returned from `{original_function}` is "
                            f"{with_article(type(item).__name__)}, but every item has to "
                            "be text, a number, a boolean, or a component."
                        ),
                        friendly_steps=(
                            "Find the item shown in the technical message "
                            "above and replace it with text, a number, a "
                            "boolean, or a component.",
                            "Convert other values to text with str().",
                        ),
                    )

        # Recursively verify each content chunk
        try:
            for chunk in self.content:
                if hasattr(chunk, "verify"):
                    chunk.verify(router, state, configuration, request)
        except Exception as e:
            return VerificationFailure(
                f"While verifying the Page() object returned from {original_function}, an error was encountered:\n"
                f"{e}",
                exception=e,
            )
        duplicate_failure = verify_unique_component_names(request, self.content)
        if duplicate_failure is not None:
            return duplicate_failure
        return None

    def format_target(self) -> str:
        """Format the target for history display, omitting the default.

        Returns:
            str: A `, target=...` snippet, or an empty string when the
            target is the default body target.
        """
        if self.target != DEFAULT_BODY_TARGET:
            return f", target={format_page_content(self.target)}"
        return ""
