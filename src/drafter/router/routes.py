"""
The Router that maps URLs to handler functions.

Defines URL normalization helpers (`normalize_url`, `clean_url`) and the
`Router` class, which stores registered routes with their introspected
signatures and prepares handler arguments by running the parameter pipeline
(collect, normalize, bind, convert, diagnose) over each incoming request.
"""

import json
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass

from drafter.config.client_server import ClientServerConfiguration
from drafter.constants import SUBMIT_BUTTON_KEY
from drafter.data.correlation import Correlation
from drafter.data.errors import (
    CATEGORY_REQUEST,
    SEVERITY_WARNING,
    ErrorDetails,
)
from drafter.data.request import Request
from drafter.history.state import SiteState
from drafter.history.utils import safe_repr
from drafter.monitor.audit import log_error
from drafter.components.utilities.registry import COMPONENT_CONTRACT_REGISTRY
from drafter.router.parameters.binding import PayloadMerger, RouteBinder
from drafter.router.parameters.collect import collect_payload, normalize_payload
from drafter.router.parameters.conversion import CONVERTER_REGISTRY
from drafter.router.parameters.diagnostics import (
    ParameterBindingError,
    RouteDiagnostic,
    partition_diagnostics,
)
from drafter.router.parameters.introspect import RouteSignatureSpec, get_signature


def normalize_url(url: str) -> str:
    """
    Turns a URL into a normalized form for consistent route matching.

    This function performs the following transformations:
    - Strips leading and trailing whitespace.
    - Strips trailing slashes.
    - Prepends "/" if the URL is non-empty and does not already start with "/".
    - Converts empty URLs to "/index".
    - Single dots are ignored
    - Double dots delete the previous path segment, if any.
    """
    url = url.strip()

    segments = []
    for segment in url.split("/"):
        if segment in ("", "."):
            continue
        elif segment == "..":
            if segments:
                segments.pop()
        else:
            segments.append(segment)

    if not segments:
        return "/index"

    normalized_url = "/" + "/".join(segments)
    return normalized_url


def clean_url(url: str) -> str:
    """
    Turns a URL into a heavily normalized form for matching against route
    function names, instead of explicit URLs.

    The following transformations are applied:
    - Strips leading and trailing whitespace.
    - Strips leading and trailing slashes.
    - Internal slashes are converted to underscores.
    - Single dots are ignored.
    - Double dots delete the previous path segment, if any.
    - Non-valid characters are removed (only alphanumeric characters and underscores are kept).
    """
    url = url.strip().strip("/")

    segments = []
    for segment in url.split("/"):
        if segment in ("", "."):
            continue
        elif segment == "..":
            if segments:
                segments.pop()
        else:
            cleaned_segment = "".join(c for c in segment if c.isalnum() or c == "_")
            segments.append(cleaned_segment)

    if not segments:
        return "index"

    cleaned_url = "_".join(segments)
    return cleaned_url


@dataclass
class Router:
    """Map URL paths to route handler functions and prepare request arguments.

    Attributes:
        routes: Dictionary mapping normalized URL strings to callable handlers.
        route_functions: Dictionary mapping cleaned function-style names to the
            same handlers, used for name-based lookup in `get_route`.
        signatures: Dictionary mapping normalized URL strings to
            RouteSignatureSpec data.
    """

    def __init__(self) -> None:
        self.routes = {}
        self.route_functions = {}
        self.signatures = {}

    def get_route(self, url: str) -> Optional[Callable]:
        """Retrieve the handler function for a given URL.

        Args:
            url: Route URL path to look up.

        Returns:
            Optional[Callable]: Handler function or None if not found.
        """
        if clean_url(url) in self.route_functions:
            return self.route_functions[clean_url(url)]
        route = self.routes.get(normalize_url(url))
        if route:
            return route
        return None

    def has_route(self, url: str) -> bool:
        """Check whether a route exists for the given URL.

        Args:
            url: Route URL path to check.

        Returns:
            bool: True if route exists, False otherwise.
        """
        return (
            clean_url(url) in self.route_functions or normalize_url(url) in self.routes
        )

    def add_route(self, url: str, func: Callable) -> dict[str, Any]:
        """Register a route handler for the given URL.

        Args:
            url: Route URL path.
            func: Handler function to call for requests to this URL.

        Returns:
            A dict with the registered "url" and the handler's "signature"
            rendered as a string.
        """
        # TODO: Handle ignored parameters.
        self.routes[normalize_url(url)] = func
        self.route_functions[clean_url(url)] = func
        self.signatures[normalize_url(url)] = get_signature(func)
        return {
            "url": url,
            "signature": self.signatures[normalize_url(url)].to_string(),
        }

    def reset(self) -> None:
        """Reset router state (currently a no-op).

        Does not remove routes or signatures.
        """

    def clear(self) -> None:
        """Remove all registered routes and signatures."""
        self.routes.clear()
        self.route_functions.clear()
        self.signatures.clear()

    def prepare_arguments(
        self,
        request: Request,
        current_state: SiteState,
        configuration: ClientServerConfiguration,
        extra_dependencies: dict[str, Any],
    ) -> tuple[list[Any], dict[str, Any], str]:
        """Prepare positional and keyword arguments for route invocation.

        Runs the deterministic five-stage parameter pipeline:

        1. Collect: build one payload (with per-key source provenance) from
           the event detail, component arguments, form fields, and framework
           metadata.
        2. Normalize: apply component-declared aliases.
        3. Bind: match payload values to the route signature, understanding
           defaults, injected dependencies (state, configuration), and
           var-keyword parameters.
        4. Convert: strictly convert explicitly typed parameters through the
           shared converter registry; pass untyped parameters through raw.
        5. Diagnose: raise on missing required parameters and failed
           conversions; warn on unused and colliding payload keys.

        Args:
            request: Incoming client request with form data.
            current_state: Current application state (injected if expected).
            configuration: Server configuration context.
            extra_dependencies: Framework values injected by parameter name.

        Returns:
            Tuple of (args list, kwargs dict, representation string).

        Raises:
            ParameterBindingError: If required parameters are missing or
                values cannot be converted to the annotated types.
        """
        signature = self.get_signature(request)

        # Stage 1: Collect (with provenance).
        scratch_kwargs = dict(request.kwargs)
        button_pressed = self.preprocess_button_press(request, scratch_kwargs)
        payload = collect_payload(request, button_pressed=button_pressed)
        # Stage 2: Normalize component-declared aliases.
        payload = normalize_payload(payload, COMPONENT_CONTRACT_REGISTRY.alias_map())
        # Stage 3 & 4: Bind to the signature and convert bound values.
        merged, merge_diagnostics = PayloadMerger().merge(
            payload, route_name=signature.function_name
        )
        bound = RouteBinder().bind(
            signature,
            merged,
            converter_registry=CONVERTER_REGISTRY,
            state=current_state,
            extra_dependencies=extra_dependencies,
        )
        # Stage 5: Diagnose.
        self.report_diagnostics(request, merge_diagnostics + bound.diagnostics)

        # Injected framework values (server, helpers like Map's add_marker)
        # are not part of the student-visible call: including them would make
        # the recorded representation un-evaluable in the debug panel.
        representable_kwargs = {
            key: value
            for key, value in bound.kwargs.items()
            if key not in extra_dependencies
        }
        representation = self.build_argument_representation(
            signature, list(bound.args), representable_kwargs
        )
        return list(bound.args), dict(bound.kwargs), representation

    def report_diagnostics(
        self, request: Request, diagnostics: tuple[RouteDiagnostic, ...]
    ) -> None:
        """Log warning diagnostics and raise if any errors were produced.

        Args:
            request: Associated request for error context.
            diagnostics: Diagnostics collected across the pipeline stages.

        Raises:
            ParameterBindingError: If any error-severity diagnostics exist.
        """
        errors, warnings = partition_diagnostics(diagnostics)
        for diagnostic in warnings:
            log_error(
                ErrorDetails(
                    id=f"request.{diagnostic.code}",
                    category=CATEGORY_REQUEST,
                    message=diagnostic.message,
                    severity=SEVERITY_WARNING,
                    details=diagnostic.hint,
                    context=Correlation(route=request.url, request_id=request.id),
                ),
                "router.prepare_arguments",
            )
        if errors:
            raise ParameterBindingError(errors)

    def build_argument_representation(
        self,
        signature: RouteSignatureSpec,
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> str:
        """Generate a string representation of function call arguments.

        Args:
            signature: Introspection data for the target function.
            args: Positional arguments list.
            kwargs: Keyword arguments dictionary.

        Returns:
            str: Function signature string like "func(arg1, kwarg=val2)".
        """
        order = {param.name: index for index, param in enumerate(signature.params)}
        show_name = {param.name: param.show_name for param in signature.params}
        rendered = [safe_repr(arg, escape=False) for arg in args]
        for key, value in sorted(
            kwargs.items(),
            key=lambda item: (order.get(item[0], len(order)), item[0]),
        ):
            if show_name.get(key, True):
                rendered.append(f"{key}={safe_repr(value, escape=False)}")
            else:
                rendered.append(safe_repr(value, escape=False))
        return f"{signature.function_name}({', '.join(rendered)})"

    def get_signature(self, request: Request) -> RouteSignatureSpec:
        """Retrieve function signature metadata for a request URL.

        Args:
            request: Request with URL to look up.

        Returns:
            RouteSignatureSpec: Signature metadata for the route.

        Raises:
            ValueError: If no signature is registered for the URL.
        """
        normalized_url = normalize_url(request.url)
        signature = self.signatures.get(normalized_url)
        if not signature:
            raise ValueError(
                f"No signature found for route '{request.url}' ('{normalized_url}')"
            )
        return signature

    def preprocess_button_press(self, request: Request, kwargs: Dict[str, Any]) -> str:
        """Extract button metadata from the request.

        Reads button_pressed from the Request object (set by the client).
        Falls back to extracting from kwargs for backward compatibility
        with older clients (e.g., the TypeScript/Skulpt bridge).

        Args:
            request: The incoming request with button_pressed field.
            kwargs: Form data dict (modified to remove button key if present as fallback).

        Returns:
            str: Button namespace/identifier, or empty string if no button.
        """
        # Prefer the client-extracted value
        if request.button_pressed:
            # Still clean up kwargs in case the key leaked through
            kwargs.pop(SUBMIT_BUTTON_KEY, None)
            return request.button_pressed

        # Fallback: extract from kwargs (for TS/Skulpt bridge compatibility)
        button_pressed = ""
        if SUBMIT_BUTTON_KEY in kwargs:
            button_value = kwargs.pop(SUBMIT_BUTTON_KEY)
            if isinstance(button_value, list) and button_value:
                button_value = button_value[0]
            try:
                button_pressed = json.loads(button_value)  # type: ignore
            except (json.JSONDecodeError, TypeError):
                button_pressed = button_value

        return button_pressed  # type: ignore
