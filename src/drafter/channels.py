"""
Channels module for bidirectional communication between client and server.

This module provides utilities for working with channels in Drafter responses.
Channels allow sending additional information alongside the main response payload,
such as scripts to run before/after rendering, audio controls, or custom data.
"""

from typing import Dict, Any, Optional


class Channels:
    """
    Helper class for working with response channels.

    Channels are a dictionary-based system for sending additional data
    with responses. Common channels include:
    - "before": Scripts to run before rendering content
    - "after": Scripts to run after rendering content
    - "audio": Audio control messages
    - "custom": Any custom data
    """

    # Standard channel names
    BEFORE = "before"
    AFTER = "after"
    AUDIO = "audio"
    CUSTOM = "custom"

    @staticmethod
    def create_empty() -> Dict[str, Any]:
        """
        Creates an empty channels dictionary.

        :return: Empty dictionary for channels.
        """
        return {}

    @staticmethod
    def add_before_script(channels: Dict[str, Any], script: str) -> Dict[str, Any]:
        """
        Adds a script to run before rendering the main content.

        :param channels: The channels dictionary to modify.
        :param script: JavaScript code to execute before rendering.
        :return: The updated channels dictionary.
        """
        if Channels.BEFORE not in channels:
            channels[Channels.BEFORE] = []
        if isinstance(channels[Channels.BEFORE], list):
            channels[Channels.BEFORE].append(script)
        else:
            channels[Channels.BEFORE] = [channels[Channels.BEFORE], script]
        return channels

    @staticmethod
    def add_after_script(channels: Dict[str, Any], script: str) -> Dict[str, Any]:
        """
        Adds a script to run after rendering the main content.

        :param channels: The channels dictionary to modify.
        :param script: JavaScript code to execute after rendering.
        :return: The updated channels dictionary.
        """
        if Channels.AFTER not in channels:
            channels[Channels.AFTER] = []
        if isinstance(channels[Channels.AFTER], list):
            channels[Channels.AFTER].append(script)
        else:
            channels[Channels.AFTER] = [channels[Channels.AFTER], script]
        return channels

    @staticmethod
    def add_audio_message(
        channels: Dict[str, Any], message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adds an audio control message.

        :param channels: The channels dictionary to modify.
        :param message: Audio control message (e.g., {"action": "play", "src": "audio.mp3"}).
        :return: The updated channels dictionary.
        """
        if Channels.AUDIO not in channels:
            channels[Channels.AUDIO] = []
        if isinstance(channels[Channels.AUDIO], list):
            channels[Channels.AUDIO].append(message)
        else:
            channels[Channels.AUDIO] = [channels[Channels.AUDIO], message]
        return channels

    @staticmethod
    def add_custom(
        channels: Dict[str, Any], name: str, data: Any
    ) -> Dict[str, Any]:
        """
        Adds custom data to a named channel.

        :param channels: The channels dictionary to modify.
        :param name: The name of the custom channel.
        :param data: The data to send on this channel.
        :return: The updated channels dictionary.
        """
        channels[name] = data
        return channels

    @staticmethod
    def get_channel(
        channels: Dict[str, Any], name: str, default: Any = None
    ) -> Any:
        """
        Retrieves data from a named channel.

        :param channels: The channels dictionary to read from.
        :param name: The name of the channel to retrieve.
        :param default: Default value if the channel doesn't exist.
        :return: The data from the channel, or the default value.
        """
        return channels.get(name, default)

    @staticmethod
    def merge_channels(
        channels1: Dict[str, Any], channels2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merges two channel dictionaries.

        For list-valued channels (before, after, audio), concatenates the lists.
        For other channels, values from channels2 override channels1.

        :param channels1: First channels dictionary.
        :param channels2: Second channels dictionary.
        :return: Merged channels dictionary.
        """
        result = dict(channels1)
        for key, value in channels2.items():
            if key in result:
                # If both are lists, concatenate
                if isinstance(result[key], list) and isinstance(value, list):
                    result[key] = result[key] + value
                # If one is a list, convert the other and concatenate
                elif isinstance(result[key], list):
                    result[key] = result[key] + [value]
                elif isinstance(value, list):
                    result[key] = [result[key]] + value
                else:
                    # Otherwise, just override
                    result[key] = value
            else:
                result[key] = value
        return result
