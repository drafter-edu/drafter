from dataclasses import dataclass


@dataclass
class BaseEvent:
    event_type: str

    def to_json(self) -> dict:
        return {
            "event_type": self.event_type,
        }
