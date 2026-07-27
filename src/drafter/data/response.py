"""
The Response dataclass, describing what the server sends back to the client:
the rendered body, status, errors/warnings, and any channel messages.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from drafter.data.channel import Channel, Message
from drafter.data.errors import STATUS_OK, ErrorDetails
from drafter.payloads.payloads import ResponsePayload

if TYPE_CHECKING:
    from drafter.payloads.target import Target


@dataclass
class Response:
    """
    Represents a response sent from the server to the client.

    Attributes:
        id: The unique identifier for this response.
        request_id: The identifier of the request this response corresponds to.
        payload: The payload content to send to the client (usually a Page).
        status_code: The symbolic status of the response (one of
            `drafter.data.errors.STATUSES`; `"ok"` for success).
        message: A human-readable message associated with the response.
        url: The URL associated with the response. Could technically be different from the request URL.
        body: The full HTML body of the response, which will be injected directly into the site's frame.
        target: An optional Target object specifying the element that the body should be injected into. If None, defaults to the body element.
        channels: A dictionary of channels for additional communication. Common
            channels include "audio", "before", and "after". The latter two are used to
            send script tags to be executed before and after the main content is rendered.
        errors: A list of canonical ErrorDetails values representing errors.
        warnings: A list of canonical ErrorDetails values representing warnings.
        metadata: A dictionary of additional metadata associated with the response.
    """

    id: int
    request_id: int
    payload: ResponsePayload
    url: str
    status_code: str = STATUS_OK
    message: str = "OK"
    body: str | None = None
    target: "Target | None" = None
    channels: dict[str, Channel] = field(default_factory=dict)
    errors: list[ErrorDetails] = field(default_factory=list)
    warnings: list[ErrorDetails] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def send_messages(self, messages: list[Message]) -> None:
        """
        Sends multiple messages through their specified channels.

        Args:
            messages: A list of Message instances to send.
        """
        for message in messages:
            self.send(message)

    def send(self, message: Message) -> None:
        """
        Sends a message through its channel, creating the channel if needed.

        The channel is determined by the message's own `channel_name`; the
        message is appended to that channel's message list.

        Args:
            message: The Message instance to send.
        """
        channel_name = message.channel_name
        if channel_name not in self.channels:
            self.channels[channel_name] = Channel(name=channel_name)
        self.channels[channel_name].messages.append(message)
