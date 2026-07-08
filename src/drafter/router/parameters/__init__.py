"""
The router-side parameter pipeline: Collect -> Normalize -> Bind -> Convert
-> Diagnose. Components define what they emit (contracts, converters); this
package owns binding payloads to route function parameters, type conversion,
and diagnostics, so route functions stay business-logic-only.
"""

from drafter.router.parameters.binding import (
    BoundArguments,
    PayloadMerger,
    RouteBinder,
)
from drafter.router.parameters.collect import collect_payload, normalize_payload
from drafter.router.parameters.conversion import (
    CONVERTER_REGISTRY,
    ConverterRegistry,
    register_shared_converters,
)
from drafter.router.parameters.diagnostics import (
    ParameterBindingError,
    RouteDiagnostic,
    format_diagnostic,
    partition_diagnostics,
)
from drafter.router.parameters.introspect import (
    RouteParamSpec,
    RouteSignatureSpec,
    get_signature,
)

__all__ = [
    "BoundArguments",
    "PayloadMerger",
    "RouteBinder",
    "collect_payload",
    "normalize_payload",
    "CONVERTER_REGISTRY",
    "ConverterRegistry",
    "register_shared_converters",
    "ParameterBindingError",
    "RouteDiagnostic",
    "format_diagnostic",
    "partition_diagnostics",
    "RouteParamSpec",
    "RouteSignatureSpec",
    "get_signature",
]
