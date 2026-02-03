from dataclasses import dataclass
from typing import Any, Optional

from drafter.components import Component
from drafter.config.client_server import ClientServerConfiguration
from drafter.history.state import SiteState
from drafter.payloads.kinds.fragment import Fragment
from drafter.payloads.target import DEFAULT_BODY_TARGET
from drafter.payloads.failure import VerificationFailure
from drafter.data.request import Request
from drafter.router.routes import Router


@dataclass
class Page(Fragment):
    """
    A page is a full-page response that replaces the entire body content.
    
    Page is a specialized Fragment that uses a default target pointing to the body element.
    This content has two critical parts:

    - The ``state``, which is the current value of the backend server for this user's session. This is used to
      restore the state of the page when the user navigates back to it. Typically, this will be a dataclass
      or a dictionary, but could also be a list, primitive value, or even None.
    - The ``content``, which is a list of strings and components that will be rendered to the user.

    The content of a page can be any combination of strings and components. Strings will be rendered as paragraphs,
    while components will be rendered as their respective HTML. Components should be classes that inherit from
    ``drafter.components.PageContent``. If the content is not a list, a ValueError will be raised.

    Args:
        state: The state of the page. If only one argument is provided, this will default to be ``None``.
        content: The content of the page. Must always be provided as a list of strings and components.
        css: Optional CSS content to inject dynamically when this page is rendered.
        js: Optional JavaScript content to inject dynamically when this page is rendered.
    """

    def __init__(self, state, content=None, css=None, js=None):
        # Page always targets the body element
        super().__init__(state, content, target=DEFAULT_BODY_TARGET, css=css, js=js)

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

        Args:
            router: The server to verify the content against.
            state: The state of the server.
            configuration: The configuration of the server.
            request: The request being processed.

        Returns:
            None if the content is valid, a VerificationFailure otherwise.
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
            from drafter.components import PageContent
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
                if hasattr(chunk, 'verify'):
                    chunk.verify(state, configuration, request)
        except Exception as e:
            return VerificationFailure(
                f"While verifying the Page() object returned from {original_function}, an error was encountered:\n"
                f"{e}"
            )
        return None
