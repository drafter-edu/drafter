from typing import Any, Optional, Callable
from dataclasses import dataclass

from drafter.data.payload import PayloadValue


@dataclass
class ConversionContext:
    """Everything a converter needs to convert one parameter value.

    The first block of fields is provided by the caller (the binder); the
    second block is filled in by the ConverterRegistry before converters run.
    """

    param_name: str
    expected_type: Any
    raw_value: Any
    payload_value: Optional[PayloadValue] = None
    route_name: str = ""

    #: The annotation with generics resolved to their origin (List[str] -> list).
    resolved_type: Any = None
    #: Type arguments of a generic annotation (List[str] -> (str,)).
    type_args: tuple = ()
    #: The registry running this conversion, for recursive element conversion.
    registry: Any = None


@dataclass
class ConversionResult:
    ok: bool
    value: Any = None
    error_code: str = ""
    message: str = ""
    hint: str = ""


#: A converter returns None when it does not apply to the given value,
#: letting the next registered converter (or the fallback) try instead.
ConverterFn = Callable[[ConversionContext], Optional[ConversionResult]]
