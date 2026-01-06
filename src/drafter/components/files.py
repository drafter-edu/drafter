from dataclasses import dataclass
import base64
import io
from typing import Union, List
from drafter.components.page_content import Component, ComponentArgument, PageContent
from drafter.components.utilities.validation import validate_parameter_name
from drafter.components.utilities.image_support import HAS_PILLOW, PILImage

# TODO: Properly handle type hints for PILImage, DrafterFile, etc.


@dataclass(repr=False)
class Download(Component):
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
        self.text = text
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.extra_settings = kwargs

    def _handle_pil_image(self, image):
        if not HAS_PILLOW or isinstance(image, str):
            return False, image

        image_data = io.BytesIO()
        image.save(image_data, format="PNG")
        image_data.seek(0)
        figure = base64.b64encode(image_data.getvalue()).decode("utf-8")
        figure = f"data:image/png;base64,{figure}"
        return True, figure

    def get_attributes(self, context) -> dict:
        attributes = super().get_attributes(context)
        was_pil, url = self._handle_pil_image(self.content)
        if was_pil:
            attributes["href"] = url
        else:
            attributes["href"] = f"data:{self.content_type},{self.content}"
        return attributes


@dataclass(repr=False)
class FileUpload(Component):
    """
    A file upload component that allows users to upload files to the server.

    The accept field can be used to specify the types of files that can be uploaded.
    It accepts either a literal string (e.g. "image/*") or a list of strings (e.g. ["image/png", "image/jpeg"]).
    You can either provide MIME types, extensions, or extensions without a period (e.g., "png", ".jpg").

    To have multiple files uploaded, use the `multiple` attribute, which will cause
    the corresponding parameter to be a list of files.
    """

    tag = "input"
    name: str

    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("accept", kind="keyword", default_value=None),
    ]

    DEFAULT_ATTRS = {"type": "file"}
    KNOWN_ATTRS = ["accept", "capture", "multiple", "required"]

    def __init__(
        self, name: str, accept: Union[str, List[str], None] = None, **extra_settings
    ):
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
