from dataclasses import dataclass
import base64
import io
from typing import Union, List
from drafter.components.page_content import Component
from drafter.components.utilities.validation import validate_parameter_name
from drafter.components.utilities.image_support import HAS_PILLOW


@dataclass
class Download(Component):
    text: str
    filename: str
    content: str
    content_type: str = "text/plain"

    def __init__(
        self, text: str, filename: str, content: str, content_type: str = "text/plain"
    ):
        self.text = text
        self.filename = filename
        self.content = content
        self.content_type = content_type

    def _handle_pil_image(self, image):
        if not HAS_PILLOW or isinstance(image, str):
            return False, image

        image_data = io.BytesIO()
        image.save(image_data, format="PNG")
        image_data.seek(0)
        figure = base64.b64encode(image_data.getvalue()).decode("utf-8")
        figure = f"data:image/png;base64,{figure}"
        return True, figure

    def __str__(self):
        was_pil, url = self._handle_pil_image(self.content)
        if was_pil:
            return f'<a download="{self.filename}" href="{url}">{self.text}</a>'
        return f'<a download="{self.filename}" href="data:{self.content_type},{self.content}">{self.text}</a>'


@dataclass
class FileUpload(Component):
    """
    A file upload component that allows users to upload files to the server.

    This works by creating a hidden input field that stores the file data as a JSON string.
    That input is sent, but the file data is not sent directly.

    The accept field can be used to specify the types of files that can be uploaded.
    It accepts either a literal string (e.g. "image/*") or a list of strings (e.g. ["image/png", "image/jpeg"]).
    You can either provide MIME types, extensions, or extensions without a period (e.g., "png", ".jpg").

    To have multiple files uploaded, use the `multiple` attribute, which will cause
    the corresponding parameter to be a list of files.
    """

    name: str
    EXTRA_ATTRS = ["accept", "capture", "multiple", "required"]

    def __init__(self, name: str, accept: Union[str, List[str], None] = None, **kwargs):
        validate_parameter_name(name, "FileUpload")
        self.name = name
        self.extra_settings = kwargs

        # Parse accept options
        if accept is not None:
            if isinstance(accept, str):
                accept = [accept]
            accept = [
                f".{ext}" if "/" not in ext and not ext.startswith(".") else ext
                for ext in accept
            ]
            self.extra_settings["accept"] = ", ".join(accept)

    def __str__(self):
        parsed_settings = self.parse_extra_settings(**self.extra_settings)
        return f"<input type='file' name={self.name!r} {parsed_settings} />"
