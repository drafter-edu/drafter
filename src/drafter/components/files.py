"""File components for downloading and uploading files.

Defines `Download`, a link that lets the user save generated content
(text or PIL images) as a file, and `FileUpload`, a form input for
accepting user file submissions.
"""

import base64
import io
from dataclasses import dataclass

from drafter.components.forms import FormComponent
from drafter.components.page_content import Component, ComponentArgument, PageContent
from drafter.components.utilities.image_support import HAS_PILLOW
from drafter.components.utilities.validation import validate_parameter_name

# TODO: Properly handle type hints for PILImage, DrafterFile, etc.


@dataclass(repr=False)
class Download(Component):
    """Creates a downloadable link for file content.

    Renders an anchor whose `href` is a data URL built from the content.
    String content is embedded directly as `data:<content_type>,<content>`.
    When Pillow is installed, a PIL Image may also be passed (despite the
    `str` annotation); it is encoded at render time as a base64 PNG data
    URL, and `content_type` is ignored. Without Pillow, non-string content
    is not converted and will not produce a usable link.

    Attributes:
        text: Display text for the download link.
        filename: Filename for the downloaded file.
        content: Content to download; a string, or a PIL Image when
            Pillow is available.
        content_type: MIME type used for string content; ignored for
            PIL Images (which always become PNG data URLs).
        tag: The HTML tag name, always 'a'.
    """

    tag = "a"
    text: PageContent
    filename: str
    content: str
    content_type: str = "text/plain"

    ARGUMENTS = [
        ComponentArgument("text", is_content=True),
        ComponentArgument("filename"),
        ComponentArgument("content"),
        ComponentArgument("content_type", kind="keyword", default_value="text/plain"),
    ]

    RENAME_ATTRS = {"filename": "download"}

    def __init__(
        self,
        text: PageContent,
        filename: str,
        content: str,
        content_type: str = "text/plain",
        **kwargs,
    ):
        """Initialize download link component.

        Args:
            text: Display text for the link.
            filename: Filename for the downloaded file.
            content: Content to download as string or PIL Image.
            content_type: MIME type of the content. Defaults to 'text/plain'.
            **kwargs: Additional HTML attributes.
        """
        self.text = text
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.extra_settings = kwargs

    def _handle_pil_image(self, image):
        """Convert PIL Image to base64-encoded data URL.

        Args:
            image: PIL Image object or string.

        Returns:
            Tuple of (was_pil, processed_url).
        """
        if not HAS_PILLOW or isinstance(image, str):
            return False, image

        image_data = io.BytesIO()
        image.save(image_data, format="PNG")
        image_data.seek(0)
        figure = base64.b64encode(image_data.getvalue()).decode("utf-8")
        figure = f"data:image/png;base64,{figure}"
        return True, figure

    def get_attributes(self, context) -> dict:
        """Get HTML attributes for the download link.

        Args:
            context: Rendering context.

        Returns:
            Dictionary including href with data URL or PIL image data.
        """
        attributes = super().get_attributes(context)
        was_pil, url = self._handle_pil_image(self.content)
        if was_pil:
            attributes["href"] = url
        else:
            attributes["href"] = f"data:{self.content_type},{self.content}"
        return attributes


@dataclass(repr=False)
class FileUpload(FormComponent):
    """File upload input for accepting user file submissions.

    Supports filtering by file type using MIME types, extensions,
    or extension without a period. Multiple files can be accepted
    with the 'multiple' attribute.

    Attributes:
        name: The form field name for the uploaded file(s).
        accept: Comma-separated file type filters rendered into the HTML
            `accept` attribute. Built from the constructor's `accept`
            argument, which may be a MIME type (e.g., 'image/*'), an
            extension (e.g., '.jpg'), or an extension without a period
            (e.g., 'png' — a period is prepended automatically). This
            attribute only exists on the instance when a non-None accept
            was given to the constructor.
        tag: The HTML tag name, always 'input'.

    Note:
        With the 'multiple' attribute, the corresponding route parameter
        is a list of files.
    """

    tag = "input"

    SELF_CLOSING_TAG = True

    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("accept", kind="keyword", default_value=None),
    ]

    DEFAULT_ATTRS = {"type": "file"}
    KNOWN_ATTRS = ["accept", "capture", "multiple", "required", "type", "name"]

    def __init__(
        self, name: str, accept: str | list[str] | None = None, **extra_settings
    ):
        """Initialize file upload component.

        Args:
            name: The form field name.
            accept: Optional file type filters (string, list of strings, or None).
            **extra_settings: Additional HTML attributes.

        Raises:
            ValueError: If name is not a valid parameter name.
        """
        validate_parameter_name(name, "FileUpload")
        self.name = name
        self.extra_settings = extra_settings

        # Parse accept options
        if accept is not None:
            if isinstance(accept, str):
                accept = [accept]
            accept = [
                f".{ext}" if "/" not in ext and not ext.startswith(".") else ext
                for ext in accept
            ]
            self.accept = ", ".join(accept)
