from typing import Any, Optional, Callable
from dataclasses import dataclass

from drafter.data.payload import PayloadValue


@dataclass
class ConversionContext:
    param_name: str
    expected_type: Any
    raw_value: Any
    payload_value: Optional[PayloadValue] = None
    route_name: str = ""


@dataclass
class ConversionResult:
    ok: bool
    value: Any = None
    error_code: str = ""
    message: str = ""
    hint: str = ""


ConverterFn = Callable[[ConversionContext], ConversionResult]
