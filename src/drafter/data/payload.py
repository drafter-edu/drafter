from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union, Literal, get_origin, get_args


PayloadSource = Literal[
    #: Custom component `args`
    "component_argument",  # data--drafter-arguments
    "event_detail",  # CustomEvent.detail
    "form_field",  # form inputs
    "framework_meta",  # request metadata injected by framework
]


@dataclass
class PayloadValue:
    name: str
    value: Any
    source: PayloadSource
    source_detail: str = ""  # e.g., component tag/id, field name, event name
