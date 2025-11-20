from typing import Any, List, Optional, Callable, Union
from dataclasses import dataclass

from drafter.components.utilities.escaping import (
    make_safe_argument,
    make_safe_json_argument,
)
from drafter.constants import JSON_DECODE_SYMBOL, LABEL_SEPARATOR, SUBMIT_BUTTON_KEY
from drafter.urls import (
    remap_attr_styles,
    friendly_urls,
    check_invalid_external_url,
    merge_url_query_params,
)
from drafter.components.page_content import Component
from drafter.components.utilities.validation import validate_parameter_name


UrlOrFunction = Union[str, Callable]


class LinkContent:
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

    EXTRA_ATTRS = ["disabled"]

    def _handle_url(self, url: UrlOrFunction, external=None) -> tuple[str, bool]:
        if callable(url):
            url = url.__name__
        if external is None:
            external = check_invalid_external_url(url) != ""
        url = url if external else friendly_urls(url)
        return url, external

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

    def create_arguments(self, arguments, label_namespace):
        parameters = self.parse_arguments(arguments, label_namespace)
        if parameters:
            return "\n".join(
                f"<input type='hidden' name='{name}' value='{make_safe_json_argument(value)}' />"
                for name, value in parameters.items()
            )
        return ""

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


RouteSafeValue = Union[str, int, float, bool]


@dataclass
class Argument(Component):
    name: str
    value: RouteSafeValue

    def __init__(self, name: str, value: RouteSafeValue, **kwargs):
        validate_parameter_name(name, "Argument")
        self.name = name
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError(
                f"Argument values must be strings, integers, floats, or booleans. Found {type(value)}"
            )
        self.value = value
        self.extra_settings = kwargs

    def __str__(self) -> str:
        value = make_safe_json_argument(self.value)
        return f"<input type='hidden' name='{JSON_DECODE_SYMBOL}{self.name}' value='{value}' {self.parse_extra_settings()} />"

    def __repr__(self) -> str:
        pieces = [repr(self.name), repr(self.value)]
        if self.extra_settings:
            for key, value in self.extra_settings.items():
                pieces.append(f"{key}={repr(value)}")
        return f"Argument({', '.join(pieces)})"


@dataclass
class Link(Component, LinkContent):
    text: str
    url: str

    def __init__(self, text: str, url: UrlOrFunction, arguments=None, **kwargs):
        self.text = text
        self.url, self.external = self._handle_url(url)
        self.extra_settings = kwargs
        self.arguments = arguments
        # Generate a unique ID for this link instance to avoid namespace collisions
        self._link_id = id(self)

    def __str__(self) -> str:
        if self.external:
            return f"<a href='{self.url}' {self.parse_extra_settings()}>{self.text}</a>"
        # Create a unique namespace using both link text and instance ID
        link_namespace = f"{self.text}#{self._link_id}"
        precode = self.create_arguments(self.arguments, link_namespace)
        value = make_safe_argument(link_namespace)
        return f"{precode}<a data-nav='{self.url}' data-submit-button='{value}' href='#' {self.parse_extra_settings()}>{self.text}</a>"

    def __repr__(self) -> str:
        pieces = [repr(self.text), repr(self.url)]
        if self.arguments:
            pieces.append(repr(self.arguments))
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"Link({', '.join(pieces)})"


@dataclass
class Button(Component, LinkContent):
    text: str
    url: str
    arguments: List[Argument]
    external: bool = False

    def __init__(self, text: str, url: UrlOrFunction, arguments=None, **kwargs):
        self.text = text
        self.url, self.external = self._handle_url(url)
        self.extra_settings = kwargs
        self.arguments = arguments or []
        # Generate a unique ID for this button instance to avoid namespace collisions
        self._button_id = id(self)

    def __repr__(self):
        pieces = [repr(self.text), repr(self.url)]
        if self.arguments:
            pieces.append(repr(self.arguments))
        for key, value in self.extra_settings.items():
            pieces.append(f"{key}={repr(value)}")
        return f"Button({', '.join(pieces)})"

    def __str__(self) -> str:
        # Create a unique namespace using both button text and instance ID
        button_namespace = f"{self.text}#{self._button_id}"
        precode = self.create_arguments(self.arguments, button_namespace)
        # Include the button ID in the button value so we know which specific button was clicked
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        value = make_safe_argument(button_namespace)
        return f"{precode}<button data-nav='{self.url}' type='submit' name='{SUBMIT_BUTTON_KEY}' value='{value}' formaction='#' {parsed_settings}>{self.text}</button>"


SubmitButton = Button
