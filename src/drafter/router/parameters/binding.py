"""
Bind stage of the parameter pipeline.

The merger resolves collisions between payload sources by precedence; the
binder matches merged payload values to route parameters (understanding
defaults, required/optional, injected dependencies, and aliases), converts
bound values through the converter registry, and emits diagnostics for
everything that doesn't line up.
"""

import difflib
from dataclasses import dataclass
from typing import Any

from drafter.data.converter import (
    ConversionContext,
    ConverterRegistry,
    preview_value,
)
from drafter.data.payload import PayloadValue, describe_source
from drafter.history.conversion import ConversionRecord, UnchangedRecord
from drafter.router.parameters.diagnostics import RouteDiagnostic
from drafter.router.parameters.introspect import RouteSignatureSpec


def _capitalize(text: str) -> str:
    return text[0].upper() + text[1:] if text else text


def _suggest(name: str, candidates: list[str]) -> str | None:
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=0.6)
    return matches[0] if matches else None


@dataclass
class BoundArguments:
    """The result of binding a request payload to a route signature.

    Attributes:
        args: Positional arguments (currently only injected state).
        kwargs: Keyword arguments, converted to the annotated types.
        diagnostics: Errors and warnings produced while binding.
        consumed_payload_keys: Payload names that bound to a parameter.
        conversions: ConversionRecord/UnchangedRecord entries for the
            debug panel.
    """

    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    diagnostics: tuple[RouteDiagnostic, ...]
    consumed_payload_keys: frozenset[str]
    conversions: tuple[Any, ...] = ()


class PayloadMerger:
    """Merge collected payload values into one value per name.

    Precedence (highest first): explicit component arguments, event detail,
    form fields, framework metadata. On a collision the higher-precedence
    value wins and a warning names both values and sources, so students can
    see why their value won.
    """

    PRECEDENCE = (
        "component_argument",
        "event_detail",
        "form_field",
        "framework_meta",
    )

    def merge(
        self, values: list[PayloadValue], route_name: str = ""
    ) -> tuple[dict[str, PayloadValue], tuple[RouteDiagnostic, ...]]:
        """Merge payload values so each name maps to exactly one value.

        When two values share a name, the one from the higher-precedence
        source (per `PRECEDENCE`; unknown sources rank last) is kept. Ties
        in precedence keep the earlier value. A `payload_collision` warning
        diagnostic is emitted for each collision where the kept and dropped
        values actually differ (values that fail equality comparison are
        treated as differing).

        Args:
            values: Collected payload values, each carrying its name,
                value, and source provenance.
            route_name: Name of the target route, used in diagnostics.

        Returns:
            Tuple of (merged dict mapping each name to its winning
            PayloadValue, tuple of warning diagnostics for collisions).
        """
        rank = {source: index for index, source in enumerate(self.PRECEDENCE)}
        merged: dict[str, PayloadValue] = {}
        diagnostics: list[RouteDiagnostic] = []
        for value in values:
            existing = merged.get(value.name)
            if existing is None:
                merged[value.name] = value
                continue
            if rank.get(existing.source, len(rank)) <= rank.get(
                value.source, len(rank)
            ):
                kept, dropped = existing, value
            else:
                kept, dropped = value, existing
            merged[value.name] = kept
            try:
                differs = kept.value != dropped.value
            except Exception:
                differs = True
            if differs:
                diagnostics.append(
                    RouteDiagnostic(
                        severity="warning",
                        code="payload_collision",
                        route_name=route_name,
                        message=(
                            f"The value '{value.name}' was provided more than "
                            f"once: {preview_value(kept.value)} from "
                            f"{describe_source(kept)} won over "
                            f"{preview_value(dropped.value)} from "
                            f"{describe_source(dropped)}."
                        ),
                        parameter=value.name,
                        source=kept.source,
                        hint=(
                            "Rename one of them if you meant them to be "
                            "different parameters."
                        ),
                    )
                )
        return merged, tuple(diagnostics)


class RouteBinder:
    """Bind a merged payload to a route signature and convert the values."""

    def bind(
        self,
        signature: RouteSignatureSpec,
        payload: dict[str, PayloadValue],
        *,
        converter_registry: ConverterRegistry,
        state: Any = None,
        extra_dependencies: dict[str, Any] | None = None,
        route_name: str = "",
    ) -> BoundArguments:
        """Bind a merged payload to a route signature and convert the values.

        Binding proceeds in stages:

        1. State injection: the first parameter receives `state` positionally
           when it is literally named "state", or when the function expects
           exactly one more parameter than the request supplied and nothing
           else (injected dependency or payload value) can fill it.
        2. Framework dependencies from `extra_dependencies` bind by exact
           parameter name and win over request data.
        3. Payload values bind to the remaining parameters by name, then by
           each parameter's declared aliases.
        4. Missing required parameters (no default, not injected) produce
           `missing_required_parameter` error diagnostics, with a
           did-you-mean hint against the leftover payload names.
        5. Leftover payload keys flow into **kwargs when the function
           accepts var-keyword arguments; otherwise each produces an
           `unused_request_parameter` warning (framework metadata is
           silently ignored).
        6. Bound payload-derived values are converted through the converter
           registry; failures produce `conversion_failed` error diagnostics.
           Injected values (state, dependencies) pass through untouched.

        Args:
            signature: Introspected signature of the target route function.
            payload: Merged payload mapping each name to one PayloadValue.
            converter_registry: Registry used to convert bound values to
                the parameters' annotated types.
            state: Current application state, injected when the signature
                expects it.
            extra_dependencies: Framework-supplied values bound by exact
                parameter name.
            route_name: Name used in diagnostics; defaults to the
                signature's function name.

        Returns:
            BoundArguments with the positional args, converted kwargs,
            all diagnostics, the set of consumed payload keys, and the
            conversion records for the debug panel.
        """
        route_name = route_name or signature.function_name
        extra_dependencies = extra_dependencies or {}
        diagnostics: list[RouteDiagnostic] = []
        conversions: list[Any] = []
        consumed: set[str] = set()
        args: list[Any] = []
        kwargs: dict[str, Any] = {}

        named = signature.named_params
        bound_names: set[str] = set()

        # State injection, preserved from the legacy router: the first
        # parameter receives state when it is literally named "state", or
        # when the function expects exactly one more parameter than the
        # request supplied (so `def route(my_state):` works with no form).
        # The arity rule yields to anything that can already fill the first
        # parameter: an injected dependency or a payload value of that name.
        request_value_count = sum(
            1 for value in payload.values() if value.source != "framework_meta"
        )
        inject_state = bool(named) and (
            named[0].name == "state"
            or (
                len(signature.params) - 1 == request_value_count
                and not named[0].injected
                and named[0].name not in extra_dependencies
                and named[0].name not in payload
            )
        )
        if inject_state:
            args.append(state)
            bound_names.add(named[0].name)

        # Framework dependencies bind by exact name and win over request data.
        for param in named:
            if param.name in bound_names:
                continue
            if param.name in extra_dependencies:
                kwargs[param.name] = extra_dependencies[param.name]
                bound_names.add(param.name)

        # Bind payload values by name, then by declared aliases.
        payload_bound: dict[str, PayloadValue] = {}
        for param in named:
            if param.name in bound_names:
                continue
            value = payload.get(param.name)
            if value is None:
                for alias in param.aliases:
                    value = payload.get(alias)
                    if value is not None:
                        break
            if value is None:
                continue
            payload_bound[param.name] = value
            consumed.add(value.name)
            bound_names.add(param.name)

        leftover = [value for name, value in payload.items() if name not in consumed]
        leftover_names = [value.name for value in leftover]

        # Missing is only an error when the parameter has no default.
        for param in named:
            if param.name in bound_names or not param.required:
                continue
            suggestion = _suggest(param.name, leftover_names)
            if suggestion:
                hint = (
                    f"Did you mean the request value '{suggestion}'? Check "
                    f"that the form field or component argument is named "
                    f"'{param.name}'."
                )
            else:
                hint = (
                    f"Add a form field, component argument, or event value "
                    f"named '{param.name}', or give the parameter a default "
                    f"value."
                )
            diagnostics.append(
                RouteDiagnostic(
                    severity="error",
                    code="missing_required_parameter",
                    route_name=route_name,
                    message=(
                        f"The route function '{route_name}' expects a value "
                        f"for parameter '{param.name}', but none was provided."
                    ),
                    parameter=param.name,
                    hint=hint,
                )
            )

        # Leftover payload keys pass into **kwargs when accepted; otherwise
        # they are dropped with a warning (framework extras never warn).
        unbound_param_names = [
            param.name for param in named if param.name not in bound_names
        ]
        for value in leftover:
            if value.source == "framework_meta":
                continue
            if signature.accepts_var_keyword:
                kwargs[value.name] = value.value
                consumed.add(value.name)
                continue
            suggestion = _suggest(
                value.name,
                unbound_param_names or [param.name for param in named],
            )
            if suggestion:
                hint = f"Did you mean the parameter '{suggestion}'?"
            else:
                hint = (
                    f"Add a parameter named '{value.name}' to '{route_name}', "
                    f"or remove the field."
                )
            diagnostics.append(
                RouteDiagnostic(
                    severity="warning",
                    code="unused_request_parameter",
                    route_name=route_name,
                    message=(
                        f"{_capitalize(describe_source(value))} was sent to "
                        f"'{route_name}', but the function has no matching "
                        f"parameter."
                    ),
                    parameter=value.name,
                    source=value.source,
                    hint=hint,
                )
            )

        # Convert only the bound, payload-derived values; injected values
        # (state, dependencies) pass through untouched.
        for param in named:
            value = payload_bound.get(param.name)
            if value is None:
                continue
            context = ConversionContext(
                param_name=param.name,
                expected_type=param.annotation,
                raw_value=value.value,
                payload_value=value,
                route_name=route_name,
            )
            result = converter_registry.convert(context)
            if not result.ok:
                diagnostics.append(
                    RouteDiagnostic(
                        severity="error",
                        code="conversion_failed",
                        route_name=route_name,
                        message=result.message,
                        parameter=param.name,
                        source=value.source,
                        hint=result.hint,
                    )
                )
                continue
            kwargs[param.name] = result.value
            if result.value is value.value:
                conversions.append(
                    UnchangedRecord(param.name, value.value, param.annotation)
                )
            else:
                conversions.append(
                    ConversionRecord(
                        param.name, value.value, param.annotation, result.value
                    )
                )

        return BoundArguments(
            args=tuple(args),
            kwargs=kwargs,
            diagnostics=tuple(diagnostics),
            consumed_payload_keys=frozenset(consumed),
            conversions=tuple(conversions),
        )
