from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Message:
    """
    Represents a message to be sent through a channel.

    :ivar content: The content of the message.
    :ivar kind: The kind of message (e.g., "script", "style").
    :ivar sigil: An optional sigil for special processing. A sigil is a marker that indicates
        whether the message has been seen or processed before; it can be used to avoid duplicate
        injections of the same content.
    """

    kind: str
    sigil: Optional[str]
    content: str


@dataclass
class Channel:
    """
    Represents a communication channel for additional content.

    :ivar name: The name of the channel.
    :ivar messages: The messages to be sent through the channel.
    """

    name: str
    messages: List[Message] = field(default_factory=list)


DEFAULT_CHANNEL_AUDIO = "audio"
DEFAULT_CHANNEL_BEFORE = "before"
DEFAULT_CHANNEL_AFTER = "after"
DEFAULT_CHANNELS = [
    DEFAULT_CHANNEL_AUDIO,
    DEFAULT_CHANNEL_BEFORE,
    DEFAULT_CHANNEL_AFTER,
]
