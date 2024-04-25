import re
from urllib.parse import urlencode, urlparse, parse_qs, quote_plus

def merge_url_query_params(url: str, additional_params: dict) -> str:
    """
    https://stackoverflow.com/a/52373377

    :param url:
    :param additional_params:
    :return:
    """
    url_components = urlparse(url)
    original_params = parse_qs(url_components.query, keep_blank_values=True)
    merged_params = dict(**original_params)
    merged_params.update(**additional_params)
    updated_query = urlencode(merged_params, doseq=True)
    return url_components._replace(query=updated_query).geturl()


def remove_url_query_params(url: str, params_to_remove: set) -> str:
    url_components = urlparse(url)
    original_params = parse_qs(url_components.query, keep_blank_values=True)
    merged_params = {k: v for k, v in original_params.items() if k not in params_to_remove}
    updated_query = urlencode(merged_params, doseq=True)
    return url_components._replace(query=updated_query).geturl()


def remap_attr_styles(attributes: dict) -> tuple[dict, dict]:
    styles, attrs = {}, {}
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
    if url.strip("/") == "index":
        return "/"
    if not url.startswith('/'):
        url = '/' + url
    return url


URL_REGEX = r"^(?:http(s)?://)[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$"

def check_invalid_external_url(url: str) -> str:
    if url.startswith("file://"):
        return "The URL references a local file on your computer, not a file on a server."
    if re.match(URL_REGEX, url) is not None:
        return "is a valid external url"
    return ""
