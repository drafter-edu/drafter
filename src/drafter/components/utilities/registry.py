"""
Registries for component-declared metadata.

Components define what they emit; these registries aggregate that metadata
at startup so the router can reason globally (binding, aliases, docs
generation, and consistency checks).

The converter registry machinery lives in the data layer
(:mod:`drafter.data.converter`), a light leaf both this layer and the router
can import eagerly; it is re-exported here so components have a natural
place to import it from when registering component-specific converters.
The router installs the shared cross-component converters into it when
:mod:`drafter.router.parameters.conversion` loads, since the router owns
conversion policy.
"""

from drafter.components.utilities.contracts import ComponentContract
from drafter.data.converter import CONVERTER_REGISTRY, ConverterRegistry

__all__ = [
    "CONVERTER_REGISTRY",
    "ConverterRegistry",
    "COMPONENT_CONTRACT_REGISTRY",
    "ComponentContractRegistry",
]


class ComponentContractRegistry:
    """Central collection of every component's declared contract."""

    def __init__(self) -> None:
        self._contracts: dict[str, ComponentContract] = {}

    def register(self, contract: ComponentContract) -> None:
        """Add (or replace) a contract, keyed by its component name.

        Args:
            contract: The contract the component declares.
        """
        self._contracts[contract.component_name] = contract

    def get(self, component_name: str) -> ComponentContract | None:
        """Look up a contract by component class name.

        Args:
            component_name: The Python class name (e.g., "Map").

        Returns:
            The registered contract, or None if the name is unknown.
        """
        return self._contracts.get(component_name)

    def all(self) -> tuple[ComponentContract, ...]:
        """Every registered contract, in registration order.

        Returns:
            Tuple of all `ComponentContract` entries.
        """
        return tuple(self._contracts.values())

    def alias_map(self) -> dict[str, str]:
        """Aggregate event-field aliases across all contracts.

        Returns:
            Mapping of alias name -> canonical field name, used by the
            router's normalize stage.
        """
        aliases: dict[str, str] = {}
        for contract in self._contracts.values():
            for event in contract.emitted_events:
                for canonical, alternates in event.aliases.items():
                    for alternate in alternates:
                        aliases[alternate] = canonical
        return aliases

    def synthetic_fields(self) -> frozenset[str]:
        """Every non-form field any component contributes to the payload."""
        return frozenset(
            name
            for contract in self._contracts.values()
            for name in contract.synthetic_fields
        )

    def helpers_for(self, html_tag: str, event_name: str) -> tuple:
        """The helpers the component with this tag provides for this event.

        Args:
            html_tag: Tag name of the element that emitted the event (any
                case; DOM tagName is uppercase).
            event_name: The event that fired (a Request's ``action``).

        Returns:
            Tuple of :class:`HelperSpec` entries whose ``events`` include
            the event (or that apply to every event).
        """
        tag = (html_tag or "").lower()
        return tuple(
            helper
            for contract in self._contracts.values()
            if contract.html_tag == tag
            for helper in contract.provided_helpers
            if not helper.events or event_name in helper.events
        )


COMPONENT_CONTRACT_REGISTRY = ComponentContractRegistry()
"""The shared registry instance: each component module registers its
CONTRACT here at import time, and the router queries it for alias maps,
synthetic fields, and event helpers."""
