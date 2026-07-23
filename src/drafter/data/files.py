"""
Dataclasses representing client file uploads. When a route parameter is
annotated with one of these types, the router's file-upload converter
turns the uploaded file into the matching dataclass.
"""

from dataclasses import dataclass


@dataclass
class DrafterBinaryFile:
    """An uploaded file with its raw binary contents.

    Attributes:
        filename: The original name of the uploaded file.
        content: The raw contents of the file.
        content_type: The MIME type reported for the file
            (defaults to "application/octet-stream").
        size: The size of the file in bytes, as reported by the client.
    """

    filename: str
    content: bytes
    content_type: str
    size: int


@dataclass
class DrafterTextFile:
    """An uploaded file with its contents decoded as UTF-8 text.

    Attributes:
        filename: The original name of the uploaded file.
        content: The contents of the file, decoded as UTF-8 text.
        content_type: The MIME type reported for the file
            (defaults to "text/plain").
        size: The size of the file, as reported by the client.
    """

    filename: str
    content: str
    content_type: str
    size: int
