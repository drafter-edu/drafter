import re
from urllib.parse import urlencode, urlparse, parse_qs


def merge_url_query_params(url: str, additional_params: dict) -> str:
    """
    Merges additional parameters into a URL. If a parameter already exists, it will be overwritten.
    For more information, see: https://stackoverflow.com/a/52373377

    Args:
        url: The URL to merge the parameters into
        additional_params: The parameters to merge into the URL.

    Returns:
        The URL with the additional parameters
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

    Args:
        url: The URL to remove the parameters from
        params_to_remove: The parameters to remove from the URL

    Returns:
        The URL with the parameters removed
    """
    url_components = urlparse(url)
    original_params = parse_qs(url_components.query, keep_blank_values=True)
    merged_params = {
        k: v for k, v in original_params.items() if k not in params_to_remove
    }
    updated_query = urlencode(merged_params, doseq=True)
    return url_components._replace(query=updated_query).geturl()


def friendly_urls(url: str) -> str:
    """
    Converts a URL to a friendly URL. This removes the leading slash and converts "index" to "/"

    Args:
        url: The URL to convert

    Returns:
        The friendly URL
    """
    url = url.strip("/")
    if url == "":
        return "index"
    return url


URL_REGEX = (
    r"^(?:http(s)?:\/\/)[\w.-]+(?:\.[\w\.-]+)+[-\w\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$"
)


def is_valid_url(url: str) -> bool:
    """
    Checks if a URL is a valid URL.

    Args:
        url: The URL to check

    Returns:
        True if the URL is valid, False otherwise
    """
    return re.match(URL_REGEX, url) is not None


def check_invalid_external_url(url: str) -> str:
    """
    Checks if a URL is a valid external URL. If it is not, it will return an error message. If it is,
    it will return an empty string.

    Args:
        url: The URL to check

    Returns:
        An error message if the URL is invalid, otherwise an empty string
    """
    if url.startswith("file://"):
        return (
            "The URL references a local file on your computer, not a file on a server."
        )
    if is_valid_url(url):
        return "is a valid external url"
    return ""


def is_external_url(url: str) -> bool:
    """
    Checks if a URL is an external URL.

    Args:
        url: The URL to check

    Returns:
        True if the URL is external, False otherwise
    """
    return url.startswith("http://") or url.startswith("https://")
