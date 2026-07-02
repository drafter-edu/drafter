from dataclasses import dataclass
from typing import Any

from drafter.router.parameters.diagnostics import RouteDiagnostic
from drafter.router.parameters.introspect import RouteSignatureSpec
from drafter.data.payload import PayloadValue
from drafter.components.utilities.registry import ConverterRegistry


@dataclass
class BoundArguments:
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    diagnostics: tuple[RouteDiagnostic, ...]
    consumed_payload_keys: frozenset[str]


class RouteBinder:
    def bind(
        self,
        signature: RouteSignatureSpec,
        payload: dict[str, PayloadValue],
        *,
        injected: dict[str, Any],
        converter_registry: ConverterRegistry,
    ) -> BoundArguments: ...


class PayloadMerger:
    PRECEDENCE = (
        "component_argument",
        "event_detail",
        "form_field",
        "framework_meta",
    )

    def merge(
        self, values: list[PayloadValue]
    ) -> tuple[dict[str, PayloadValue], tuple[RouteDiagnostic, ...]]: ...
