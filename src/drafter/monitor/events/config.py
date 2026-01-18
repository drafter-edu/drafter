from dataclasses import dataclass
from typing import Any, Optional

from drafter.monitor.events.base import BaseEvent


@dataclass
class UpdatedConfigurationEvent(BaseEvent):
    event_type: str = "ConfigurationUpdated"
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
class ResetServerEvent(BaseEvent):
    event_type: str = "ResetServer"

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
        }
