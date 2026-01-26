from dataclasses import dataclass
import base64
import io
from typing import Optional
from drafter.components.utilities.image_support import HAS_PILLOW, PILImage
from drafter.components.page_content import Component, ComponentArgument
from drafter.components.links import LinkContent, UrlOrFunction
from drafter.components.planning.render_plan import RenderPlan
from drafter.helpers.urls import check_invalid_external_url, friendly_urls

BASE_IMAGE_FOLDER = "/__images"


@dataclass(repr=False)
class Image(Component):
    """Renders an image element with support for local paths and PIL images.

    Supports external URLs, local file paths, and PIL Image objects
    (when Pillow is installed). PIL images are automatically converted
    to base64-encoded data URLs.

    Attributes:
        url: The image URL, local path, or PIL Image object.
        width: Optional width in pixels.
        height: Optional height in pixels.
        tag: The HTML tag name, always 'img'.
        SELF_CLOSING_TAG: Indicates this is a self-closing tag.
    """
    url: str
    width: Optional[int]
    height: Optional[int]

    tag = "img"
    SELF_CLOSING_TAG = True
    KNOWN_ATTRS = ["src", "width", "height", "alt"]
    RENAME_ATTRS = {"url": "src"}

    ARGUMENTS = [
        ComponentArgument("url"),
        ComponentArgument("width", kind="keyword", default_value=None),
        ComponentArgument("height", kind="keyword", default_value=None),
    ]

    def __init__(self, url: str, width=None, height=None, **kwargs):
        """Initialize image component.

        Args:
            url: The image URL, local file path, or PIL Image object.
            width: Optional width in pixels.
            height: Optional height in pixels.
            **kwargs: Additional HTML attributes (e.g., alt text).
        """
        self.url = url
        self.width = width
        self.height = height
        self.extra_settings = kwargs
        self.base_image_folder = BASE_IMAGE_FOLDER

    def open(self, *args, **kwargs):
        """Open an image file using PIL.

        Args:
            *args: Positional arguments for PIL Image.open().
            **kwargs: Keyword arguments for PIL Image.open().

        Returns:
            A PIL Image object.

        Raises:
            ImportError: If Pillow is not installed.
        """
        if not HAS_PILLOW:
            raise ImportError(
                "Pillow is not installed. Please install it to use this feature."
            )
        return PILImage.open(*args, **kwargs)

    def new(self, *args, **kwargs):
        """Create a new image using PIL.

        Args:
            *args: Positional arguments for PIL Image.new().
            **kwargs: Keyword arguments for PIL Image.new().

        Returns:
            A new PIL Image object.

        Raises:
            ImportError: If Pillow is not installed.
        """
        if not HAS_PILLOW:
            raise ImportError(
                "Pillow is not installed. Please install it to use this feature."
            )
        return PILImage.new(*args, **kwargs)

    def _handle_pil_image(self, image):
        """Convert a PIL Image to a base64-encoded data URL.

        Args:
            image: A PIL Image object or string.

        Returns:
            Tuple of (was_pil, processed_url) where was_pil indicates
            if the input was a PIL image.
        """
        if not HAS_PILLOW or isinstance(image, str):
            return False, image

        # print("Handling PIL image.", image)
        image_data = io.BytesIO()
        image.save(image_data, format="PNG")
        image_data.seek(0)
        figure = base64.b64encode(image_data.getvalue()).decode("utf-8")
        # figure = base64.b64encode(image["content"])
        figure = f"data:image/png;base64,{figure}"
        return True, figure

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

        try:
            was_pil, url = self._handle_pil_image(self.url)
        except Exception as e:
            # Return an error message
            if "alt" not in attributes:
                attributes["alt"] = "Error loading image: " + str(e)
            return attributes

        if was_pil:
            attributes["src"] = url
        else:
            url_processed, external = self._handle_url(self.url)
            if not external:
                # Ensure we have a leading slash
                if not url_processed.startswith("/"):
                    url_processed = "/" + url_processed
                url_processed = self.base_image_folder + url_processed
            attributes["src"] = url_processed

        return attributes


Picture = Image
