"""Argument component for passing data to routes."""

from dataclasses import dataclass
from typing import Any

from drafter.components.base import PageContent, validate_parameter_name, make_safe_json_argument
from drafter.constants import JSON_DECODE_SYMBOL


@dataclass
class Argument(PageContent):
    name: str
    value: Any

    def __init__(self, name: str, value: Any, **kwargs):
        validate_parameter_name(name, "Argument")
        self.name = name
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError(f"Argument values must be strings, integers, floats, or booleans. Found {type(value)}")
        self.value = value
        self.extra_settings = kwargs

    def __str__(self) -> str:
        value = make_safe_json_argument(self.value)
        return f"<input type='hidden' name='{JSON_DECODE_SYMBOL}{self.name}' value='{value}' {self.parse_extra_settings()} />"
