import html
import json


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
