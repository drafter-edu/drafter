import json
from typing import List, Callable, Union, Optional
from dataclasses import dataclass
import html

from drafter.components.planning.render_plan import RenderPlan
from drafter.components.utilities.escaping import (
    make_safe_argument,
    make_safe_json_argument,
)
from drafter.constants import SUBMIT_BUTTON_KEY
from drafter.helpers.urls import (
    friendly_urls,
    check_invalid_external_url,
)
from drafter.components.page_content import (
    Arguable,
    ArgumentList,
    Component,
    ComponentArgument,
    JsonSafeValue,
    UrlOrFunction,
)
from drafter.components.utilities.validation import (
    validate_json_value,
    validate_parameter_name,
)


@dataclass(repr=False)
class Argument(Component, Arguable):
    """Hidden form input for passing arguments to route handlers.

    Attributes:
        tag: The HTML tag name, always 'input'.
        DEFAULT_ATTRS: Default attributes {'type': 'hidden'}.
        name: The name of the argument parameter.
        value: The JSON-safe value of the argument.
    """

    tag = "input"

    DEFAULT_ATTRS = {"type": "hidden"}
    KNOWN_ATTRS = ["type", "name", "value"]
    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("value"),
    ]

    def __init__(self, name: str, value: JsonSafeValue, **extra_settings):
        """Initialize argument component.

        Args:
            name: The parameter name for the argument.
            value: The JSON-safe value to pass.
            **extra_settings: Additional HTML attributes.

        Raises:
            ValueError: If name or value are not valid.
        """
        validate_parameter_name(name, "Argument")
        validate_json_value(value, "Argument")
        self.name = name
        self.value = value
        self.extra_settings = extra_settings

    def get_attributes(self, context) -> dict:
        """Get HTML attributes for the argument input.

        Args:
            context: Rendering context.

        Returns:
            Dictionary of HTML attributes including encoded name and value.
        """
        attributes = super().get_attributes(context)
        attributes["name"] = f"{self.name}"
        attributes["value"] = json.dumps(self.value)
        attributes["data-transform"] = "json-decode"
        return attributes

    def get_id(self) -> str:
        """Get the identifier for this argument.

        Returns:
            The element ID or the argument name.
        """
        return self.extra_settings.get("id", self.name)


class LinkContent(Component):
    """Base class for link and button components with URL handling.

    Provides shared functionality for verifying URLs, handling both
    internal and external links, and managing associated arguments.

    Attributes:
        url: The URL or route name for the link.
        text: The display text for the link.
    """

    url: str
    text: str

    KNOWN_ATTRS = ["disabled"]

    def _handle_url(self, url: UrlOrFunction, external=None) -> tuple[str, bool]:
        """Process URL, converting functions to names and handling internal routes.

        Args:
            url: The URL, route name, or callable.
            external: Whether URL is external; auto-detected if None.

        Returns:
            Tuple of (processed_url, is_external).
        """
        if callable(url):
            url = url.__name__
        if external is None:
            external = check_invalid_external_url(url) != ""
        url = url if external else friendly_urls(url)
        return url, external

    def get_link_namespace(self):
        """Generate a unique identifier for this link.

        Returns:
            String combining text and element ID for uniqueness.
        """
        return f"{self.text}#{self.get_id()}"

    def get_attributes(self, context) -> dict:
        """Get HTML attributes for the link.

        Args:
            context: Rendering context.

        Returns:
            Dictionary including data-nav attribute with URL.
        """
        attributes = super().get_attributes(context)
        attributes["data-nav"] = self.url
        return attributes

    def verify(self, router, state, configuration, request):
        if not router.has_route(self.url):
            invalid_external_url_reason = check_invalid_external_url(self.url)
            if invalid_external_url_reason == "is a valid external url":
                return None
            elif invalid_external_url_reason:
                raise ValueError(
                    f"Link `{self.url}` is not a valid external url.\n{invalid_external_url_reason}."
                )
            raise ValueError(
                f"Link `{self.text}` points to non-existent page `{self.url}`."
            )
        return None


@dataclass(repr=False)
class Link(LinkContent):
    text: str
    url: str
    external: bool = False

    tag = "a"

    KNOWN_ATTRS = ["href", "target", "rel", "download", "formaction", "disabled"]
    DEFAULT_ATTRS = {"href": "#", "formaction": "#"}
    RENAME_ATTRS = {"url": "href"}

    ARGUMENTS = [
        ComponentArgument("text", is_content=True),
        ComponentArgument("url"),
        ComponentArgument("arguments", kind="keyword", default_value=None),
        ComponentArgument("external", kind="keyword", default_value=False),
    ]

    def __init__(
        self,
        text: str,
        url: UrlOrFunction,
        arguments: ArgumentList = None,
        external: bool = False,
        **extra_settings,
    ):
        self.text = text
        self.url, self.external = self._handle_url(url, external)
        self.extra_settings = extra_settings
        if arguments is not None:
            self.extra_settings["arguments"] = arguments

    def get_attributes(self, context) -> dict:
        # TODO: Handle external links correctly
        # TODO: Handle the configuration setting that blocks external links
        attributes = super().get_attributes(context)
        attributes["name"] = SUBMIT_BUTTON_KEY
        attributes["data-submit-button"] = make_safe_argument(self.get_link_namespace())
        return attributes


@dataclass(repr=False)
class Button(LinkContent):
    """Renders a clickable button that navigates to a route or URL.

    Attributes:
        text: The display text for the button.
        url: The target URL or route name.
        arguments: Optional list of Argument objects to pass to the route.
        external: Whether the URL is external (auto-detected if not provided).
        tag: The HTML tag name, always 'button'.
    """

    text: str
    url: str
    arguments: Optional[List[Argument]] = None
    external: bool = False

    tag = "button"

    KNOWN_ATTRS = ["type", "name", "formaction", "disabled"]
    DEFAULT_ATTRS = {"formaction": "#", "type": "submit"}
    RENAME_ATTRS = {"url": "data-nav", "arguments": ""}
    ARGUMENTS = [
        ComponentArgument("text", is_content=True),
        ComponentArgument("url"),
        ComponentArgument("arguments", kind="keyword", default_value=None),
    ]

    # TODO: Verify that the button does not have any interactive content as children

    def __init__(
        self,
        text: str,
        url: UrlOrFunction,
        arguments: ArgumentList = None,
        **extra_settings,
    ):
        """Initialize button component.

        Args:
            text: The display text for the button.
            url: The target route or URL (function names are converted to strings).
            arguments: Optional arguments to pass to the target route.
            **extra_settings: Additional HTML attributes and styles.
        """
        self.text = text
        self.url, self.external = self._handle_url(url)
        self.extra_settings = extra_settings
        if arguments is not None:
            self.extra_settings["arguments"] = arguments

    def get_attributes(self, context) -> dict:
        """Get HTML attributes for the button.

        Args:
            context: Rendering context.

        Returns:
            Dictionary including submit button data.
        """
        attributes = super().get_attributes(context)
        attributes["name"] = SUBMIT_BUTTON_KEY
        attributes["value"] = make_safe_argument(self.get_link_namespace())
        return attributes


SubmitButton = Button
