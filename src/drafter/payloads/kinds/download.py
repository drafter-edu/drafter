"""The `Download` payload for triggering a file download in the browser."""

from dataclasses import dataclass

from PIL import Image as PILImage

from drafter.data.images import Picture
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Download(ResponsePayload):
    """
    A Download is a payload that will trigger a file download in the browser.

    The payload bundles both the file's origin and its data: `file_path`
    records where the file came from on the server (or virtual filesystem),
    while `content` holds the actual data delivered to the browser, so the
    file does not need to be read again at download time. The browser saves
    the data under `file_name`.

    A `Picture` (or PIL Image) may be given as the content; it is encoded
    to file bytes using its own MIME type, which also fills in an empty
    `mime_type`, and its filename fills in an empty `file_name`.

    Attributes:
        file_path: Path of the source file the download originates from.
        file_name: Name the browser should use when saving the file.
        mime_type: MIME type of the content (e.g., `text/plain`).
        content: The file data to deliver, as bytes, a string, or a
            `Picture`/PIL Image.

    Example:
        def download_report(state):
            return Download(
                "report.txt",
                "my_report.txt",
                "text/plain",
                "Sales were up 10% this quarter.",
            )
    """

    file_path: str
    file_name: str
    mime_type: str
    content: bytes | str

    def __post_init__(self):
        """Encode Picture/PIL content to bytes, filling empty metadata."""
        content = self.content
        if isinstance(content, PILImage.Image):
            content = Picture(content)
        if isinstance(content, Picture):
            if not self.mime_type:
                self.mime_type = content.mime_type
            if not self.file_name and content.filename:
                self.file_name = content.filename
            self.content = content.to_bytes()
