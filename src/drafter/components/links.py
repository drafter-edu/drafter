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
from drafter.components.page_content import Component, ComponentArgument, PageContent
from drafter.components.utilities.validation import validate_parameter_name


RouteSafeValue = Union[str, int, float, bool]
UrlOrFunction = Union[str, Callable]


@dataclass(repr=False)
class Argument(Component):
    name: str
    value: RouteSafeValue

    tag = "input"

    DEFAULT_ATTRS = {"type": "hidden"}
    KNOWN_ATTRS = ["type", "name", "value"]
    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("value"),
    ]

    def __init__(self, name: str, value: RouteSafeValue, **extra_settings):
        validate_parameter_name(name, "Argument")
        self.name = name
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError(
                f"Argument values must be strings, integers, floats, or booleans. Found {type(value)}"
            )
        self.value = value
        self.extra_settings = extra_settings

    def get_attributes(self, context) -> dict:
        attributes = super().get_attributes(context)
        attributes["name"] = f"{JSON_DECODE_SYMBOL}{self.name}"
        attributes["value"] = make_safe_json_argument(self.value)
        return attributes


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
    arguments: Optional[List[Argument]] = None

    KNOWN_ATTRS = ["disabled"]
    RENAME_ATTRS = {"arguments": "data--drafter-arguments"}

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
        if self.arguments:
            attributes["data--drafter-arguments"] = make_safe_json_argument(
                {arg.name: arg.value for arg in self.arguments}
            )
        return attributes

    def plan(self, context) -> RenderPlan:
        button_plan = super().plan(context)
        if not self.arguments:
            return button_plan
        # Create a unique namespace using both button text and instance ID
        button_namespace = self.get_link_namespace()
        argument_plans = self.plan_arguments(self.arguments, button_namespace)
        return RenderPlan(kind="fragment", items=[button_plan, *argument_plans])

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

    def plan_arguments(self, arguments, label_namespace):
        parameters = self.parse_arguments(arguments, label_namespace)
        if parameters:
            return [
                RenderPlan(
                    kind="tag",
                    tag_name="input",
                    attributes={
                        "type": "hidden",
                        "name": name,
                        "value": make_safe_json_argument(value),
                    },
                    known_attributes=["type", "name", "value"],
                )
                for name, value in parameters.items()
            ]
        return []

    def parse_arguments(self, arguments, label_namespace):
        if arguments is None:
            return {}
        if isinstance(arguments, dict):
            return arguments
        if isinstance(arguments, Argument):
            escaped_label_namespace = make_safe_argument(label_namespace)
            return {
                f"{escaped_label_namespace}{LABEL_SEPARATOR}{arguments.name}": arguments.value
            }
        if isinstance(arguments, list):
            result = {}
            escaped_label_namespace = make_safe_argument(label_namespace)
            for arg in arguments:
                if isinstance(arg, Argument):
                    arg, value = arg.name, arg.value
                else:
                    arg, value = arg
                result[f"{escaped_label_namespace}{LABEL_SEPARATOR}{arg}"] = value
            return result
        raise ValueError(
            f"Could not create arguments from the provided value: {arguments}"
        )


@dataclass(repr=False)
class Link(LinkContent):
    text: str
    url: str
    arguments: Optional[List[Argument]] = None
    external: bool = False

    tag = "a"

    KNOWN_ATTRS = ["href", "target", "rel", "download", "formaction", "disabled"]
    DEFAULT_ATTRS = {"href": "#", "formaction": "#"}
    RENAME_ATTRS = {"url": "href", "arguments": "data--drafter-arguments"}

    ARGUMENTS = [
        ComponentArgument("text"),
        ComponentArgument("url"),
        ComponentArgument("arguments", kind="keyword", default_value=None),
    ]

    def __init__(self, text: str, url: UrlOrFunction, arguments=None, **kwargs):
        self.text = text
        self.url, self.external = self._handle_url(url)
        self.extra_settings = kwargs
        self.arguments = arguments

    def get_attributes(self, context) -> dict:
        attributes = super().get_attributes(context)
        # TODO: Change to using data--drafter-arguments and handle in the frontend
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
    RENAME_ATTRS = {"url": "data-nav", "arguments": "data--drafter-arguments"}
    ARGUMENTS = [
        ComponentArgument("text"),
        ComponentArgument("url"),
        ComponentArgument("arguments", kind="keyword", default_value=None),
    ]

    # TODO: Verify that the button does not have any interactive content as children

    def __init__(self, text: str, url: UrlOrFunction, arguments=None, **kwargs):
        self.text = text
        self.url, self.external = self._handle_url(url)
        self.extra_settings = kwargs
        self.arguments = arguments

    def get_attributes(self, context) -> dict:
        attributes = super().get_attributes(context)
        attributes["name"] = SUBMIT_BUTTON_KEY
        attributes["value"] = make_safe_argument(self.get_link_namespace())
        return attributes


SubmitButton = Button
