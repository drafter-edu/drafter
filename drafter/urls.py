from typing import Any, Tuple, Dict
import re
from urllib.parse import urlencode, urlparse, parse_qs

def merge_url_query_params(url: str, additional_params: dict) -> str:
    """
    Merges additional parameters into a URL. If a parameter already exists, it will be overwritten.
    For more information, see: https://stackoverflow.com/a/52373377

    :param url: The URL to merge the parameters into
    :param additional_params: The parameters to merge into the URL.
    :return: The URL with the additional parameters
    """
    url_components = urlparse(url)
    original_params = parse_qs(url_components.query, keep_blank_values=True)
    merged_params = dict(**original_params)
    merged_params.update(**additional_params)
    updated_query = urlencode(merged_params, doseq=True)
    return url_components._replace(query=updated_query).geturl()


def remove_url_query_params(url: str, params_to_remove: set) -> str:
    """
    Removes parameters from a URL. If a parameter does not exist, it will be ignored.

    :param url: The URL to remove the parameters from
    :param params_to_remove: The parameters to remove from the URL
    :return: The URL with the parameters removed
    """
    url_components = urlparse(url)
    original_params = parse_qs(url_components.query, keep_blank_values=True)
    merged_params = {k: v for k, v in original_params.items() if k not in params_to_remove}
    updated_query = urlencode(merged_params, doseq=True)
    return url_components._replace(query=updated_query).geturl()


def remap_attr_styles(attributes: dict) -> Tuple[dict, dict]:
    """
    Remaps attributes into styles and attributes dictionaries. This is useful for handling style and class attributes.
    The 'classes' key's vales will be moved to 'class' and joined with a space. Any key prefixed with 'style_' will be
    moved to the styles dictionary. All other keys will be moved to the attributes dictionary.

    :param attributes: The attributes to remap
    :return: A tuple of the styles and attributes dictionaries
    """
    styles: Dict[str, Any] = {}
    attrs: Dict[str, Any] = {}
    # Handle classes keyword
    if 'classes' in attributes:
        attributes['class'] = attributes.pop('classes')
        if isinstance(attributes['class'], list):
            attributes['class'] = " ".join(attributes['class'])
    # Handle styles_ prefixed keyword
    for key, value in attributes.items():
        target = attrs
        if key.startswith("style_"):
            key = key[len("style_"):]
            target = styles
        key = key.replace("_", "-")
        target[key] = value
    # All done
    return styles, attrs


def friendly_urls(url: str) -> str:
    """
    Converts a URL to a friendly URL. This removes the leading slash and converts "index" to "/"

    :param url: The URL to convert
    :return: The friendly URL
    """
    if url.strip("/") == "index":
        return "/"
    if not url.startswith('/'):
        url = '/' + url
    return url


URL_REGEX = r"^(?:http(s)?://)[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$"


def is_valid_url(url: str) -> bool:
    """
    Checks if a URL is a valid URL.

    :param url: The URL to check
    :return: True if the URL is valid, False otherwise
    """
    return re.match(URL_REGEX, url) is not None


def check_invalid_external_url(url: str) -> str:
    """
    Checks if a URL is a valid external URL. If it is not, it will return an error message. If it is,
    it will return an empty string.

    :param url: The URL to check
    :return: An error message if the URL is invalid, otherwise an empty string
    """
    if url.startswith("file://"):
        return "The URL references a local file on your computer, not a file on a server."
    if is_valid_url(url):
        return "is a valid external url"
    return ""

def is_external_url(url: str) -> bool:
    """
    Checks if a URL is an external URL.

    :param url: The URL to check
    :return: True if the URL is external, False otherwise
    """
    return url.startswith("http://") or url.startswith("https://")
