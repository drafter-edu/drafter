"""The `Download` payload for triggering a file download in the browser."""

from typing import Union
from dataclasses import dataclass
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

    Attributes:
        file_path: Path of the source file the download originates from.
        file_name: Name the browser should use when saving the file.
        mime_type: MIME type of the content (e.g., `text/plain`).
        content: The file data to deliver, as bytes or a string.

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
    content: Union[bytes, str]
