from dataclasses import dataclass, field
from textwrap import indent
from typing import Any, Dict, List, Optional, Union

from drafter.components.links import LinkContent
from drafter.data.channel import Message
from drafter.config.client_server import ClientServerConfiguration
from drafter.configuration import ServerConfiguration
from drafter.constants import RESTORABLE_STATE_KEY
from drafter.components import Component, PageContent, Link
from drafter.data.request import Request
from drafter.history.formatting import format_page_content
from drafter.history.state import SiteState
from drafter.payloads.renderer import render, Renderer
from drafter.payloads.payloads import ResponsePayload
from drafter.payloads.target import Target
from drafter.payloads.failure import VerificationFailure
from drafter.router.routes import Router


@dataclass
class Fragment(ResponsePayload):
    """
    A Fragment is a payload that will render a fragment of HTML to be injected
    into an existing page, rather than a full page by itself.

    This is the base payload class. Content is rendered to HTML and injected into
    a specified target element on the page.

    Args:
        state: The state of the fragment. If only one argument is provided, this will default to be ``None``.
        content: The content of the fragment. Must always be provided as a list of strings and components.
        target: The target element to inject into. Can be a Target instance, a string ID/selector, or None.
        css: Optional CSS content to inject dynamically when this fragment is rendered.
        js: Optional JavaScript content to inject dynamically when this fragment is rendered.
    """

    state: Any
    content: list
    target: Optional[Union[Target, str]] = None
    css: Optional[List[str]] = None
    js: Optional[List[str]] = None

    def __init__(self, state, content=None, target=None, css=None, js=None):
        if content is None:
            state, content = None, state
        self.state = state
        self.content = content
        self.target = target
        self.css = css
        self.js = js

        if isinstance(content, (str, Component)):
            # If the content is a single string, convert it to a list with that string as the only element.
            self.content = [content]
        elif not isinstance(content, list):
            incorrect_type = type(content).__name__
            raise ValueError(
                "The content of a Fragment must be a list of strings or components."
                f" Found {incorrect_type} instead."
            )
        else:
            for index, chunk in enumerate(content):
                if not isinstance(chunk, (str, Component)):
                    incorrect_type = type(chunk).__name__
                    raise ValueError(
                        "The content of a Fragment must be a list of strings or components."
                        f" Found {incorrect_type} at index {index} instead."
                    )

    def get_state_updates(self) -> tuple[bool, Any]:
        return True, self.state

    def render(
        self, state: SiteState, configuration: ClientServerConfiguration
    ) -> Optional[str]:
        """
        Renders the content of the fragment to HTML.
        Users should not call this method directly; it will be called on their behalf by the server.

        Args:
            state: The current state of the server. This will be used to restore the page if needed.
            configuration: The configuration of the server. This will be used to determine how the fragment is rendered.

        Returns:
            A string of HTML representing the content of the fragment.
        """
        content = render(
            self.content,
            state,
            configuration,
        )
        if self.js is None:
            self.js = []
        elif isinstance(self.js, str):
            self.js = [self.js]
        if self.css is None:
            self.css = []
        elif isinstance(self.css, str):
            self.css = [self.css]
        self.js.extend(content.assets["js"])
        self.css.extend(content.assets["css"])
        return content.flatten()
    
    def format_target(self) -> str:
        return f", target={format_page_content(self.target)}"
    
    def format(
        self,
        state: SiteState,
        representation: str,
        configuration: ClientServerConfiguration,
    ) -> str:
        """
        Formats the payload for display in the history panel.
        Essentially, the result should be a `repr` that could be used to recreate
        the payload.
        """
        pieces = [format_page_content(self.state)]
        if isinstance(self.content, list):
            pieces.append(", [\n")
            for item in self.content:
                pieces.append(indent(format_page_content(item), " " * 4))
                pieces.append(",\n")
            pieces.append("]")
        else:
            pieces.append(f",\n")
            pieces.append(indent(format_page_content(self.content), " " * 4))

        if self.target is not None:
            pieces.append(self.format_target())
        if self.css:
            pieces.append(f", css={format_page_content(self.css)}")
        if self.js:
            pieces.append(f", js={format_page_content(self.js)}")
            
        class_name = self.__class__.__name__

        return "".join(
            [
                "assert_equal(",
                representation + ",\n",
                indent(f"{class_name}({''.join(pieces)})", " " * 4),
                ")",
            ]
        )

    def get_messages(
        self,
        state: SiteState,
        configuration: ClientServerConfiguration,
    ) -> list[Message]:
        # Add CSS as style messages in the "before" channel
        messages = []
        if self.css:
            if isinstance(self.css, str):
                self.css = [self.css]
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
        if self.js:
            if isinstance(self.js, str):
                self.js = [self.js]
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

    def get_target(self, request: Request) -> Optional[Target]:
        """
        Gets the target element that this Fragment should be injected into.
        If None, the Fragment will be injected into the requesting element's dom_id.

        Returns:
            A Target instance or None. Converts string selectors to Target objects.
        """
        target = self.target

        if target is None:
            # Check if the request has a dom_id to target
            if request.dom_id:
                return Target(id=request.dom_id)
            else:
                return None

        # Convert string selectors to Target objects
        if isinstance(target, str):
            # Parse the string selector into a Target
            selector = target.strip()
            if selector.startswith("#"):
                return Target(id=selector[1:])
            elif selector.startswith("."):
                return Target(class_name=selector[1:])
            elif selector.startswith("[") and selector.endswith("]"):
                # Handle data attributes and other attributes
                attr_content = selector[1:-1]
                if "=" in attr_content:
                    attr_key, attr_val = attr_content.split("=", 1)
                    return Target(
                        attribute={attr_key.strip(): attr_val.strip().strip("'\"")}
                    )
                else:
                    return Target(data_attribute=attr_content)
            else:
                # Treat as a tag or custom selector
                return Target(selector=selector)

        # Already a Target object
        return target

    def verify(
        self,
        router: Router,
        state: SiteState,
        configuration: ClientServerConfiguration,
        request: Request,
    ) -> Optional[VerificationFailure]:
        """
        Verifies that the content of the fragment is valid. This will check that all links are valid and that
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
        if isinstance(self.content, str):
            content_to_verify = [self.content]
        elif not isinstance(self.content, list):
            return VerificationFailure(
                f"Expected content to be a list, but got {type(self.content).__name__}"
            )
        else:
            content_to_verify = self.content

        # Recursively verify each content chunk
        try:
            for chunk in content_to_verify:
                if isinstance(chunk, LinkContent):
                    chunk.verify(router, state, configuration, request)
        except Exception as e:
            return VerificationFailure(f"Error verifying fragment content: {str(e)}")
        return None
