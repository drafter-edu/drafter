"""Image components for displaying pictures on pages.

Defines `Image`, which renders an image element from a `Picture` value,
an external URL, a local file path, raw image bytes, or a PIL image.
The `Picture` value type itself lives in `drafter.data.images`; a
`Picture` placed directly in page content is automatically wrapped in an
`Image` component.
"""

import warnings
from dataclasses import dataclass

from PIL import Image as PILImage

from drafter.components.data.photo import Photo
from drafter.components.page_content import Component, ComponentArgument, UrlOrFunction
from drafter.data.images import Picture, bytes_to_data_url, sniff_image_mime
from drafter.helpers.urls import check_invalid_external_url, friendly_urls, is_data_url


@dataclass(repr=False)
class Image(Component):
    """Renders an image element from a value or a URL.

    Accepts a `Picture` value, an external URL, a local file path, a data
    URL, raw image bytes, or a PIL Image object. Values (Pictures, bytes,
    PIL images) are converted to base64-encoded data URLs at render time;
    URL-backed Pictures and plain URL/path strings render as URLs.

    Attributes:
        url: The image source: URL, local path, Picture, bytes, or PIL Image.
        width: Optional width in pixels.
        height: Optional height in pixels.
        tag: The HTML tag name, always 'img'.
        SELF_CLOSING_TAG: Indicates this is a self-closing tag.
    """

    url: str | bytes | Picture | PILImage.Image | Photo
    width: int | None
    height: int | None

    tag = "img"
    SELF_CLOSING_TAG = True
    KNOWN_ATTRS = ["src", "width", "height", "alt"]
    RENAME_ATTRS = {"url": "src"}

    ARGUMENTS = [
        ComponentArgument("url"),
        ComponentArgument("width", kind="keyword", default_value=None),
        ComponentArgument("height", kind="keyword", default_value=None),
    ]

    def __init__(
        self,
        url: str | bytes | Picture | PILImage.Image | Photo,
        width=None,
        height=None,
        **kwargs,
    ):
        """Initialize image component.

        Args:
            url: The image source: URL, local file path, data URL,
                `Picture`, raw image bytes, or PIL Image object.
            width: Optional width in pixels.
            height: Optional height in pixels.
            **kwargs: Additional HTML attributes (e.g., alt text).
        """
        self.url = url
        self.width = width
        self.height = height
        self.extra_settings = kwargs

    def open(self, *args, **kwargs):
        """Open an image file using PIL. Deprecated: use ``Picture(...)``.

        Args:
            *args: Positional arguments for PIL Image.open().
            **kwargs: Keyword arguments for PIL Image.open().

        Returns:
            A PIL Image object.
        """
        warnings.warn(
            "Image.open() is deprecated; use Picture(filename) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return PILImage.open(*args, **kwargs)

    def new(self, *args, **kwargs):
        """Create a new image using PIL. Deprecated: use ``Picture.new(...)``.

        Args:
            *args: Positional arguments for PIL Image.new().
            **kwargs: Keyword arguments for PIL Image.new().

        Returns:
            A new PIL Image object.
        """
        warnings.warn(
            "Image.new() is deprecated; use Picture.new(width, height) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return PILImage.new(*args, **kwargs)

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

    def get_attributes(self, context) -> dict:
        """Get HTML attributes for the image.

        Args:
            context: Rendering context.

        Returns:
            Dictionary of HTML attributes including src.
        """
        attributes = super().get_attributes(context)

        source = self.url
        try:
            if isinstance(source, PILImage.Image):
                source = Picture(source)
            elif isinstance(source, (bytes, bytearray)):
                mime = sniff_image_mime(bytes(source))
                if mime:
                    attributes["src"] = bytes_to_data_url(bytes(source), mime)
                    return attributes
                source = Picture(bytes(source))

            if isinstance(source, Photo) and source.picture is not None:
                source = source.picture

            if isinstance(source, Picture):
                if "alt" not in attributes and source.filename:
                    attributes["alt"] = source.filename
                if source.url is not None:
                    # URL-backed and unmodified: let the browser fetch it.
                    attributes["src"] = source.url
                else:
                    attributes["src"] = source.to_data_url()
                return attributes
        except Exception as e:
            if "alt" not in attributes:
                attributes["alt"] = "Error loading image: " + str(e)
            return attributes

        if not isinstance(source, Photo) and is_data_url(source):
            attributes["src"] = source
            return attributes

        if not isinstance(source, Photo):
            url_processed, external = self._handle_url(source)
            if not external:
                # Ensure we have a leading slash
                if not url_processed.startswith("/"):
                    url_processed = "/" + url_processed
            attributes["src"] = url_processed

        return attributes
