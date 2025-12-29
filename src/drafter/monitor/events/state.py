from dataclasses import dataclass
from typing import Any, Optional

from drafter.monitor.events.base import BaseEvent
from drafter.history.utils import safe_repr
from drafter.monitor.events.recursive_type_describer import RecursiveTypeDescriber


@dataclass
class UpdatedStateEvent(BaseEvent):
    html: str = ""
    event_type: str = "UpdatedState"
    table: Optional[dict[str, Any]] = None

    def to_json(self) -> dict[str, Any]:
        return {
            **super().to_json(),
            "html": self.html,
            "table": self.table or {"columns": ["Field", "Type", "Value"], "rows": []},
        }

    @classmethod
    def from_state(cls, state: Any) -> "UpdatedStateEvent":
        html = f"<pre>{safe_repr(state)}</pre>"
        describer = RecursiveTypeDescriber(max_depth=4)
        table = describer.describe_table(state)
        return cls(html=html, table=table)
