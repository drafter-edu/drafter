from typing import Optional, Union
from dataclasses import dataclass
from drafter.payloads.payloads import ResponsePayload


@dataclass
class Download(ResponsePayload):
    """
    A Download is a payload that will trigger a file download in the browser.
    """

    file_path: str
    file_name: str
    mime_type: str
    content: Union[bytes, str]
