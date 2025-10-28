"""Base classes and utilities for Drafter components."""

from dataclasses import dataclass
from typing import Any, Union, Optional, List
import html
import json

from drafter.constants import LABEL_SEPARATOR, SUBMIT_BUTTON_KEY, JSON_DECODE_SYMBOL
from drafter.urls import remap_attr_styles, friendly_urls, check_invalid_external_url, merge_url_query_params
from drafter.history import safe_repr


BASELINE_ATTRS = ["id", "class", "style", "title", "lang", "dir", "accesskey", "tabindex", "value",
                  "onclick", "ondblclick", "onmousedown", "onmouseup", "onmouseover", "onmousemove", "onmouseout",
                  "onkeypress", "onkeydown", "onkeyup",
                  "onfocus", "onblur", "onselect", "onchange", "onsubmit", "onreset", "onabort", "onerror", "onload",
                  "onunload", "onresize", "onscroll",
                  "accesskey", "anchor", "role", "spellcheck", "tabindex",
                  ]


BASE_PARAMETER_ERROR = ("""The {component_type} name must be a valid Python identifier name. A string is considered """
                        """a valid identifier if it only contains alphanumeric letters (a-z) and (0-9), or """
                        """underscores (_). A valid identifier cannot start with a number, or contain any spaces.""")


def validate_parameter_name(name: str, component_type: str):
    """
    Validates a parameter name to ensure it adheres to Python's identifier naming rules.
    The function verifies if the given name is a string, non-empty, does not contain spaces,
    does not start with a digit, and is a valid Python identifier. Additionally, it ensures
    the name starts with a letter or an underscore. Raises a `ValueError` with a detailed
    error message if validation fails.

    :param name: The name to validate.
    :type name: str
    :param component_type: Describes the type of component associated with the parameter.
    :type component_type: str
    :raises ValueError: If `name` is not a string, is empty, contains spaces, starts with a
        digit, does not start with a letter or underscore, or is not a valid identifier.
    """
    base_error = BASE_PARAMETER_ERROR.format(component_type=component_type)
    if not isinstance(name, str):
        raise ValueError(base_error + f"\n\nReason: The given name `{name!r}` is not a string.")
    if not name.isidentifier():
        if " " in name:
            raise ValueError(base_error + f"\n\nReason: The name `{name}` has a space, which is not allowed.")
        if not name:
            raise ValueError(base_error + f"\n\nReason: The name is an empty string.")
        if name[0].isdigit():
            raise ValueError(base_error + f"\n\nReason: The name `{name}` starts with a digit, which is not allowed.")
        if not name[0].isalpha() and name[0] != "_":
            raise ValueError(base_error + f"\n\nReason: The name `{name}` does not start with a letter or an underscore.")
        raise ValueError(base_error + f" The name `{name}` is not a valid Python identifier name.")


class PageContent:
    """
    Base class for all content that can be added to a page.
    This class is not meant to be used directly, but rather to be subclassed by other classes.
    Critically, each subclass must implement a ``__str__`` method that returns the HTML representation.

    Under most circumstances, a string value can be used in place of a ``PageContent`` object
    (in which case we say it is a ``Content`` type). However, the ``PageContent`` object
    allows for more customization and control over the content.

    Ultimately, the ``PageContent`` object is converted to a string when it is rendered.

    This class also has some helpful methods for verifying URLs and handling attributes/styles.
    """
    EXTRA_ATTRS: List[str] = []
    extra_settings: dict

    def verify(self, server) -> bool:
        """
        Verify the status of this component. This method is called before rendering the component
        to ensure that the component is in a valid state. If the component is not valid, this method
        should return False.

        Default implementation returns True.

        :param server: The server object that is rendering the component
        :return: True if the component is valid, False otherwise
        """
        return True

    def parse_extra_settings(self, **kwargs):
        """
        Parses and combines extra settings into valid attribute and style formats.

        This method processes additional configuration settings provided via arguments or stored
        in the `extra_settings` property, converts them into valid HTML attributes and styles,
        and then consolidates the processed values into the appropriate output format. Attributes
        not explicitly defined in the baseline or extra attribute lists are converted into inline
        style declarations.

        :param kwargs: Arbitrary keyword arguments containing extra configuration settings to be
            applied or overridden. The keys represent attribute or style names, and the values
            represent their corresponding values.
        :return: A string containing formatted HTML attributes along with an inline style block
            if any styles are provided.
        :rtype: str
        """
        extra_settings = self.extra_settings.copy()
        extra_settings.update(kwargs)
        raw_styles, raw_attrs = remap_attr_styles(extra_settings)
        styles, attrs = [], []
        for key, value in raw_attrs.items():
            if key not in self.EXTRA_ATTRS and key not in BASELINE_ATTRS:
                styles.append(f"{key}: {value}")
            else:
                # TODO: Is this safe enough?
                attrs.append(f"{key}={str(value)!r}")
        for key, value in raw_styles.items():
            styles.append(f"{key}: {value}")
        result = " ".join(attrs)
        if styles:
            result += f" style='{'; '.join(styles)}'"
        return result

    def update_style(self, style, value):
        """
        Updates the style of a specific setting and stores it in the
        extra_settings dictionary with a key formatted as "style_{style}".

        :param style: The key representing the style to be updated
        :type style: str
        :param value: The value to associate with the given style key
        :type value: Any
        :return: Returns the instance of the object after updating the style
        :rtype: self
        """
        self.extra_settings[f"style_{style}"] = value
        return self

    def update_attr(self, attr, value):
        """
        Updates a specific attribute with the given value in the extra_settings dictionary.

        This method modifies the `extra_settings` dictionary by setting the specified
        attribute to the given value. It returns the instance of the object, allowing
        for method chaining. No validation is performed on the input values, so they
        should conform to the expected structure or constraints of the `extra_settings`.

        :param attr: The key of the attribute to be updated in the dictionary.
        :type attr: str
        :param value: The value to set for the specified key in the dictionary.
        :type value: Any
        :return: The instance of the object after the update.
        :rtype: Self
        """
        self.extra_settings[attr] = value
        return self

    def render(self, current_state, configuration):
        """
        This method is called when the component is being rendered to a string. It should return
        the HTML representation of the component, using the current State and configuration to
        determine the final output.

        :param current_state: The current state of the component
        :type current_state: Any
        :param configuration: The configuration settings for the component
        :type configuration: Configuration
        :return: The HTML representation of the component
        """
        return str(self)


Content = Union[PageContent, str]


def make_safe_json_argument(value):
    """
    Converts the given value to a JSON-compatible string and escapes special
    HTML characters, making it safe for inclusion in HTML contexts.

    :param value: The input value to be converted and escaped. The value can
        be of any type that is serializable to JSON.
    :return: An HTML-safe JSON string representation of the input value.
    """
    return html.escape(json.dumps(value), True)


def make_safe_argument(value):
    """
    Encodes the given value into JSON format and escapes any special HTML
    characters to ensure the argument is safe for use in HTML contexts.

    This function is particularly useful in scenarios where you need
    to serialize a Python object into JSON, while making sure that the
    output is safe to insert into an HTML document, protecting against
    potential HTML injection attacks.

    :param value: Any Python object that needs to be converted to a
        JSON string and HTML escaped.
    :type value: Any
    :return: A string containing the HTML-escaped and JSON-encoded
        representation of the input value.
    :rtype: str
    """
    return html.escape(json.dumps(value), True)


def make_safe_name(value):
    """
    This function takes a value as input and generates a safe string version of it by escaping
    special characters to prevent injection attacks or unintended HTML rendering. It ensures that
    the provided input is safely transformed into an escaped HTML string.

    :param value: The input value to be escaped. It is converted to a string if it is not already.
    :type value: Any
    :return: The escaped HTML version of the input value as a string.
    :rtype: str
    """
    return html.escape(str(value))


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

    def _handle_url(self, url, external=None):
        if callable(url):
            url = url.__name__
        if external is None:
            external = check_invalid_external_url(url) != ""
        url = url if external else friendly_urls(url)
        return url, external

    def verify(self, server) -> bool:
        if self.url not in server._handle_route:
            invalid_external_url_reason = check_invalid_external_url(self.url)
            if invalid_external_url_reason == "is a valid external url":
                return True
            elif invalid_external_url_reason:
                raise ValueError(f"Link `{self.url}` is not a valid external url.\n{invalid_external_url_reason}.")
            raise ValueError(f"Link `{self.text}` points to non-existent page `{self.url}`.")
        return True

    def create_arguments(self, arguments, label_namespace):
        parameters = self.parse_arguments(arguments, label_namespace)
        if parameters:
            return "\n".join(f"<input type='hidden' name='{name}' value='{make_safe_json_argument(value)}' />"
                             for name, value in parameters.items())
        return ""

    def parse_arguments(self, arguments, label_namespace):
        if arguments is None:
            return {}
        if isinstance(arguments, dict):
            return arguments
        # Import here to avoid circular dependency
        from drafter.components.argument import Argument
        if isinstance(arguments, Argument):
            escaped_label_namespace = make_safe_argument(label_namespace)
            return {f"{escaped_label_namespace}{LABEL_SEPARATOR}{arguments.name}": arguments.value}
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
        raise ValueError(f"Could not create arguments from the provided value: {arguments}")
