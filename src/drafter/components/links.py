from typing import List, Callable, Union, Optional
from dataclasses import dataclass
import html

from drafter.components.planning.render_plan import RenderPlan
from drafter.components.utilities.escaping import (
    make_safe_argument,
    make_safe_json_argument,
)
from drafter.constants import JSON_DECODE_SYMBOL, LABEL_SEPARATOR, SUBMIT_BUTTON_KEY
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
    tag = "input"

    DEFAULT_ATTRS = {"type": "hidden"}
    KNOWN_ATTRS = ["type", "name", "value"]
    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("value"),
    ]

    def __init__(self, name: str, value: JsonSafeValue, **extra_settings):
        validate_parameter_name(name, "Argument")
        validate_json_value(value, "Argument")
        self.name = name
        self.value = value
        self.extra_settings = extra_settings

    def get_attributes(self, context) -> dict:
        attributes = super().get_attributes(context)
        attributes["name"] = f"{JSON_DECODE_SYMBOL}{self.name}"
        attributes["value"] = make_safe_json_argument(self.value)
        return attributes

    def get_id(self) -> str:
        return self.extra_settings.get("id", self.name)


class LinkContent(Component):
    """
    Represents content for a hyperlink.

    This class encapsulates the URL and display text of a link.
    It provides utility methods for verifying the URL, handling its structure,
    and processing associated arguments.

    :ivar url: The URL of the link.
    :type url: str
    :ivar text: The display text of the link.
    :type text: str
    """

    url: str
    text: str

    KNOWN_ATTRS = ["disabled"]

    def _handle_url(self, url: UrlOrFunction, external=None) -> tuple[str, bool]:
        if callable(url):
            url = url.__name__
        if external is None:
            external = check_invalid_external_url(url) != ""
        url = url if external else friendly_urls(url)
        return url, external

    def get_link_namespace(self):
        return f"{self.text}#{self.get_id()}"

    def get_attributes(self, context) -> dict:
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
        ComponentArgument("text"),
        ComponentArgument("url"),
        ComponentArgument("arguments", kind="keyword", default_value=None),
    ]

    def __init__(
        self,
        text: str,
        url: UrlOrFunction,
        arguments: ArgumentList = None,
        **extra_settings,
    ):
        self.text = text
        self.url, self.external = self._handle_url(url)
        self.extra_settings = extra_settings
        if arguments is not None:
            self.extra_settings["arguments"] = arguments

    def get_attributes(self, context) -> dict:
        attributes = super().get_attributes(context)
        attributes["name"] = SUBMIT_BUTTON_KEY
        attributes["data-submit-button"] = make_safe_argument(self.get_link_namespace())
        return attributes


@dataclass(repr=False)
class Button(LinkContent):
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
        self.text = text
        self.url, self.external = self._handle_url(url)
        self.extra_settings = extra_settings
        if arguments is not None:
            self.extra_settings["arguments"] = arguments

    def get_attributes(self, context) -> dict:
        attributes = super().get_attributes(context)
        attributes["name"] = SUBMIT_BUTTON_KEY
        attributes["value"] = make_safe_argument(self.get_link_namespace())
        return attributes


SubmitButton = Button
