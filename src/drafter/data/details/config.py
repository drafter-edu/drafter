from dataclasses import dataclass
from typing import Any, Optional

from drafter.data.telemetry import TelemetryRecord


@dataclass
class InitialConfigurationEvent(TelemetryRecord):
    kind: str = "InitialConfiguration"
    config: Optional[dict[str, Any]] = None

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "config": self.config,
        }


@dataclass
class UpdatedConfigurationEvent(TelemetryRecord):
    kind: str = "UpdatedConfiguration"
    key: Optional[str] = None
    value: Optional[Any] = None
    update_default: bool = False

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "key": self.key,
            "value": self.value,
            "update_default": self.update_default,
        }


@dataclass
class ResetServerEvent(TelemetryRecord):
    kind: str = "ResetServer"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
        }


@dataclass
class ServerInitializedEvent(TelemetryRecord):
    kind: str = "ServerInitialized"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
        }
