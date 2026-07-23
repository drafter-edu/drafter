"""
Channels and messages for sending auxiliary content (such as scripts,
styles, and audio) to the client alongside a response's main body.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Message:
    """
    Represents a message to be sent through a channel.

    Attributes:
        channel_name: The name of the channel through which the message will be sent.
        content: The content of the message.
        kind: The kind of message (e.g., "script", "style").
        sigil: An optional sigil for special processing. A sigil is a marker that indicates
            whether the message has been seen or processed before; it can be used to avoid duplicate
            injections of the same content.
    """

    channel_name: str
    kind: str
    sigil: Optional[str]
    content: str


@dataclass
class Channel:
    """
    Represents a communication channel for additional content.

    Attributes:
        name: The name of the channel.
        messages: The messages to be sent through the channel.
    """

    name: str
    messages: List[Message] = field(default_factory=list)


DEFAULT_CHANNEL_AUDIO = "audio"
"""Channel carrying audio content for the client to play."""
DEFAULT_CHANNEL_BEFORE = "before"
"""Channel whose messages are injected before the page content is rendered."""
DEFAULT_CHANNEL_AFTER = "after"
"""Channel whose messages are injected after the page content is rendered."""
DEFAULT_CHANNELS = [
    DEFAULT_CHANNEL_AUDIO,
    DEFAULT_CHANNEL_BEFORE,
    DEFAULT_CHANNEL_AFTER,
]
"""The channel names that Drafter itself uses when building responses."""
