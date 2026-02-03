from dataclasses import dataclass, field
from typing import Dict, Optional, TYPE_CHECKING
from drafter.data.channel import Channel, Message
from drafter.monitor.events.errors import DrafterError, DrafterWarning
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
        status_code: The status code of the response.
        message: A human-readable message associated with the response.
        url: The URL associated with the response. Could technically be different from the request URL.
        body: The full HTML body of the response, which will be injected directly into the site's frame.
        target: An optional Target object specifying the element that the body should be injected into. If None, defaults to the body element.
        channels: A dictionary of channels for additional communication. Common
            channels include "audio", "before", and "after". The latter two are used to
            send script tags to be executed before and after the main content is rendered.
        errors: A list of DrafterError instances representing errors that occurred.
        warnings: A list of DrafterWarning instances representing warnings that occurred.
        metadata: A dictionary of additional metadata associated with the response.
    """

    id: int
    request_id: int
    payload: ResponsePayload
    url: str
    status_code: int = 200
    message: str = "OK"
    body: Optional[str] = None
    target: "Optional[Target]" = None
    channels: Dict[str, Channel] = field(default_factory=dict)
    errors: list[DrafterError] = field(default_factory=list)
    warnings: list[DrafterWarning] = field(default_factory=list)
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
        Sends a message through the specified channel.

        Args:
            channel_name: The name of the channel to send the message through.
            message: The content of the message to send.
            kind: The kind of message (default is "script").
            sigil: An optional sigil for special processing.
        """
        channel_name = message.channel_name
        if channel_name not in self.channels:
            self.channels[channel_name] = Channel(name=channel_name)
        self.channels[channel_name].messages.append(message)
