"""
Configuration and server lifecycle events for tracking setup,
reconfiguration, and resets.
"""

from dataclasses import dataclass
from typing import Any, Optional

from drafter.data.telemetry import TelemetryRecord


@dataclass
class InitialConfigurationEvent(TelemetryRecord):
    """
    Event emitted when the server applies its initial configuration.

    Attributes:
        config: JSON representation of the full initial configuration
    """

    kind: str = "InitialConfiguration"
    config: Optional[dict[str, Any]] = None

    def to_json(self) -> dict[str, Any]:
        """
        Converts the InitialConfigurationEvent instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the event.
        """
        return {
            **super().to_json(),
            "config": self.config,
        }


@dataclass
class UpdatedConfigurationEvent(TelemetryRecord):
    """
    Event emitted when a configuration setting is updated.

    Attributes:
        key: Name of the configuration setting that changed
        value: The new value of the setting
        update_default: Whether the default configuration was also updated,
            affecting future server instances
    """

    kind: str = "UpdatedConfiguration"
    key: Optional[str] = None
    value: Optional[Any] = None
    update_default: bool = False

    def to_json(self) -> dict[str, Any]:
        """
        Converts the UpdatedConfigurationEvent instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the event.
        """
        return {
            **super().to_json(),
            "key": self.key,
            "value": self.value,
            "update_default": self.update_default,
        }


@dataclass
class ResetServerEvent(TelemetryRecord):
    """
    Event emitted when the server's state and request history are reset.
    """

    kind: str = "ResetServer"

    def to_json(self) -> dict[str, Any]:
        """
        Converts the ResetServerEvent instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the event.
        """
        return {
            **super().to_json(),
        }


@dataclass
class ServerInitializedEvent(TelemetryRecord):
    """
    Event emitted when a server instance is first created.
    """

    kind: str = "ServerInitialized"

    def to_json(self) -> dict[str, Any]:
        """
        Converts the ServerInitializedEvent instance to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the event.
        """
        return {
            **super().to_json(),
        }
